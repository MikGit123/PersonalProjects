from django.db import models
import random
import string

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase, k=4))

class Question(models.Model):
    text = models.CharField(max_length=255)
    def __str__(self): return self.text

class Room(models.Model):
    code = models.CharField(max_length=4, default=generate_code, unique=True)
    question_count = models.IntegerField(default=3)
    
class Player(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='players')
    name = models.CharField(max_length=50)
    channel_name = models.CharField(max_length=255)
    target = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL)

class Answer(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    question_text = models.CharField(max_length=255)
    text = models.CharField(max_length=255)