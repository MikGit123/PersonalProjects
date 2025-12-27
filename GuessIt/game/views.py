

# Create your views here.
from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def room(request, room_code):
    return render(request, 'room.html', {'room_code': room_code})