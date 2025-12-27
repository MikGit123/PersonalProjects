import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .templates.game.models import Room, Player, Answer

class GameConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group = f'game_{self.room_code}'

        # Join the "Group" (Room)
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    # Handles incoming messages from JavaScript
    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data['action']

        if action == 'joinGame':
            await self.join_game(data['name'])
        elif action == 'startGame':
            await self.start_game()
        elif action == 'submitAnswer':
            await self.submit_answer(data['answer'])

    # --- Game Logic Methods ---

    async def join_game(self, name):
        # Save player to DB
        await self.db_create_player(name)
        # Broadcast to everyone in room
        await self.broadcast_message('playerJoined', {'name': name})

    async def start_game(self):
        # Assign targets (A -> B, B -> C)
        assignments = await self.db_assign_targets()
        
        # Send specific target to each player privately
        for channel, target_name in assignments.items():
            await self.channel_layer.send(channel, {
                'type': 'game_event',
                'event_type': 'startRound',
                'data': {'target': target_name}
            })

    async def submit_answer(self, text):
        count = await self.db_save_answer(text)
        # If everyone has answered, reveal them
        if await self.db_check_all_answered(count):
            answers = await self.db_get_all_answers()
            await self.broadcast_message('revealAnswers', {'answers': answers})

    # --- Helper to send to group ---
    async def broadcast_message(self, event_type, data):
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type': 'game_event',
                'event_type': event_type,
                'data': data
            }
        )

    # Actual WebSocket sender
    async def game_event(self, event):
        await self.send(text_data=json.dumps({
            'type': event['event_type'],
            'data': event['data']
        }))

    # --- Database Interactions (Must be synchronous) ---

    @database_sync_to_async
    def db_create_player(self, name):
        room, _ = Room.objects.get_or_create(code=self.room_code)
        self.player = Player.objects.create(room=room, name=name, channel_name=self.channel_name)

    @database_sync_to_async
    def db_assign_targets(self):
        room = Room.objects.get(code=self.room_code)
        players = list(room.players.all())
        mapping = {}
        if len(players) < 2: return {} # Need 2 players minimum
        
        for i, p in enumerate(players):
            target = players[(i + 1) % len(players)] # Next player in circle
            p.target = target
            p.save()
            mapping[p.channel_name] = target.name
        return mapping

    @database_sync_to_async
    def db_save_answer(self, text):
        Answer.objects.create(player=self.player, text=text)
        return Answer.objects.filter(player__room__code=self.room_code).count()

    @database_sync_to_async
    def db_check_all_answered(self, count):
        return count == Room.objects.get(code=self.room_code).players.count()

    @database_sync_to_async
    def db_get_all_answers(self):
        # Returns list of {writer: 'Name', subject: 'TargetName', answer: 'Text'}
        answers = Answer.objects.filter(player__room__code=self.room_code)
        return [{'writer': a.player.name, 'subject': a.player.target.name, 'text': a.text} for a in answers]