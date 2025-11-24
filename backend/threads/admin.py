from django.contrib import admin
from .models import Thread, Message


@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['id', 'pdf', 'page_number', 'selection_text', 'created_by', 'created_at', 'last_activity_at']
    list_filter = ['created_at', 'workspace', 'pdf']
    search_fields = ['selection_text', 'pdf__title']
    readonly_fields = ['created_at', 'last_activity_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'thread', 'sender', 'content', 'created_at', 'edited_at']
    list_filter = ['created_at', 'thread']
    search_fields = ['content', 'sender__username']
    readonly_fields = ['created_at']

