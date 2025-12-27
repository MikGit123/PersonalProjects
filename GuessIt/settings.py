INSTALLED_APPS = [
    'daphne',          # MUST be at the top for WebSockets
    'channels',        # WebSocket handling
    'game',            # Your app
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Add this block at the very bottom of the file
ASGI_APPLICATION = 'guessit_project.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}