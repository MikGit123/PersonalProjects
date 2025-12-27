from django.contrib import admin
from .models import Question, Room, Player, Answer

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text',)

admin.site.register(Room)
admin.site.register(Player)
admin.site.register(Answer)