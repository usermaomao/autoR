from django.contrib import admin
from .models import Deck, Card, ReviewLog


@admin.register(Deck)
class DeckAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'daily_new_limit', 'daily_review_limit', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'name', 'description')
        }),
        ('配置', {
            'fields': ('daily_new_limit', 'daily_review_limit')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ('word', 'card_type', 'state', 'user', 'deck', 'ef', 'interval', 'lapses', 'due_at')
    list_filter = ('card_type', 'state', 'user', 'deck', 'created_at')
    search_fields = ('word', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'deck', 'word', 'card_type', 'state')
        }),
        ('SM-2 算法字段', {
            'fields': ('ef', 'interval', 'difficulty', 'stability', 'lapses', 'due_at', 'learning_step')
        }),
        ('元数据', {
            'fields': ('metadata', 'tags', 'notes')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReviewLog)
class ReviewLogAdmin(admin.ModelAdmin):
    list_display = ('card', 'user', 'quality', 'time_taken', 'reviewed_at')
    list_filter = ('quality', 'user', 'reviewed_at')
    search_fields = ('card__word',)
    readonly_fields = ('reviewed_at',)
    fieldsets = (
        ('基本信息', {
            'fields': ('card', 'user', 'quality', 'time_taken', 'reviewed_at')
        }),
        ('复习前状态', {
            'fields': ('before_state', 'before_ef', 'before_interval', 'before_due_at')
        }),
        ('复习后状态', {
            'fields': ('after_state', 'after_ef', 'after_interval', 'after_due_at')
        }),
    )

