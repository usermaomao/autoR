from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Deck, Card, ReviewLog


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    class Meta:
        model = User
        fields = ('id', 'username', 'email')
        read_only_fields = ('id',)


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm')

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("密码不匹配")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class DeckSerializer(serializers.ModelSerializer):
    """卡组序列化器"""
    user = UserSerializer(read_only=True)
    card_count = serializers.SerializerMethodField()

    class Meta:
        model = Deck
        fields = ('id', 'user', 'name', 'description', 'daily_new_limit',
                  'daily_review_limit', 'card_count', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

    def get_card_count(self, obj):
        return obj.cards.count()


class CardSerializer(serializers.ModelSerializer):
    """卡片序列化器"""
    user = UserSerializer(read_only=True)
    deck_name = serializers.CharField(source='deck.name', read_only=True)
    card_type_display = serializers.CharField(source='get_card_type_display', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Card
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')


class CardListSerializer(serializers.ModelSerializer):
    """卡片列表序列化器（简化版）"""
    deck_name = serializers.CharField(source='deck.name', read_only=True)
    card_type_display = serializers.CharField(source='get_card_type_display', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Card
        fields = ('id', 'word', 'card_type', 'card_type_display', 'state',
                  'state_display', 'deck', 'deck_name', 'ef', 'interval',
                  'lapses', 'due_at', 'created_at')


class ReviewLogSerializer(serializers.ModelSerializer):
    """复习记录序列化器"""
    card_word = serializers.CharField(source='card.word', read_only=True)
    quality_display = serializers.CharField(source='get_quality_display', read_only=True)

    class Meta:
        model = ReviewLog
        fields = '__all__'
        read_only_fields = ('id', 'user', 'reviewed_at')
