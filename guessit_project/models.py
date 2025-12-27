from django.db import models
import random
import string

# Generates a random 4-letter room code (e.g., "ABXY")
def generate_code():
    return ''.join(random.choices(string.ascii_uppercase, k=4))

class Room(models.Model):
    code = models.CharField(max_length=4, default=generate_code, unique=True)

class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=50)
    channel_name = models.CharField(max_length=255) # WebSocket ID
    
    # The person this player must answer questions about
    target = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

class Answer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    
    # Helper to print readable string
    def __str__(self):
        return f"{self.player.name}: {self.text}"