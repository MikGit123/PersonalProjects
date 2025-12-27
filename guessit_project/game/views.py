from django.shortcuts import render

def index(request):
    return render(request, 'game/index.html')

def room(request, room_code):
    return render(request, 'game/room.html', {'room_code': room_code})