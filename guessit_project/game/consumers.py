import json, random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Room, Player, Answer, Question

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group = f'game_{self.room_code}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data['action']

        if action == 'joinGame':
            await self.join_game(data['name'])
        elif action == 'startGame':
            count = int(data.get('questionCount', 3))
            await self.start_game(count)
        elif action == 'submitAnswer':
            await self.submit_answer(data['answer'], data['question'])

    async def join_game(self, name):
        await self.create_player(name)
        await self.broadcast('playerJoined', {'name': name})

    async def start_game(self, count):
        questions = await self.get_random_questions(count)
        assignments = await self.assign_targets()
        await self.channel_layer.group_send(self.room_group, {
            'type': 'game.message', 
            'event_type': 'gameStarted',
            'data': {'questions': questions, 'assignments': assignments}
        })

    async def submit_answer(self, text, question_text):
        finished = await self.save_answer(text, question_text)
        if finished:
            all_answers = await self.get_all_answers()
            await self.broadcast('revealAnswers', {'answers': all_answers})

    async def broadcast(self, event_type, data):
        await self.channel_layer.group_send(self.room_group, {
            'type': 'game.message', 'event_type': event_type, 'data': data
        })

    async def game_message(self, event):
        if 'assignments' in event['data']:
            my_target = event['data']['assignments'].get(self.channel_name)
            event['data']['your_target'] = my_target
        await self.send(text_data=json.dumps({'type': event['event_type'], 'data': event['data']}))

    @database_sync_to_async
    def create_player(self, name):
        room, _ = Room.objects.get_or_create(code=self.room_code)
        self.player = Player.objects.create(room=room, name=name, channel_name=self.channel_name)

    @database_sync_to_async
    def get_random_questions(self, count):
        pks = list(Question.objects.values_list('pk', flat=True))
        random.shuffle(pks)
        selected_pks = pks[:count]
        return list(Question.objects.filter(pk__in=selected_pks).values_list('text', flat=True))

    @database_sync_to_async
    def assign_targets(self):
        room = Room.objects.get(code=self.room_code)
        players = list(room.players.all())
        mapping = {}
        if len(players) < 2: return {}
        for i, p in enumerate(players):
            target = players[(i+1)%len(players)]
            p.target = target
            p.save()
            mapping[p.channel_name] = target.name
        return mapping

    @database_sync_to_async
    def save_answer(self, text, q_text):
        Answer.objects.create(player=self.player, text=text, question_text=q_text)
        room = Room.objects.get(code=self.room_code)
        current = Answer.objects.filter(player__room=room, question_text=q_text).count()
        return current >= room.players.count()

    @database_sync_to_async
    def get_all_answers(self):
        answers = Answer.objects.filter(player__room__code=self.room_code)
        return [{'writer': a.player.name, 'subject': a.player.target.name, 'text': a.text, 'question': a.question_text} for a in answers]