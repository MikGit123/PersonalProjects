from django.contrib import admin
from django.urls import path, include  # <-- Add include here

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('game.urls')),    # <-- This connects the game app
]