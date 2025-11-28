from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Deck, Card, ReviewLog, AIConfig
from .services.svg_generator import generate_svg_card
from datetime import datetime


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

    def _generate_and_attach_svg(self, instance):
        """生成并附加 SVG 到 metadata"""
        try:
            svg_front, svg_back = generate_svg_card(
                word=instance.word,
                card_type=instance.card_type,
                metadata=instance.metadata
            )

            # 更新 metadata
            if not instance.metadata:
                instance.metadata = {}

            instance.metadata['svg_front'] = svg_front
            instance.metadata['svg_back'] = svg_back
            instance.metadata['svg_generated_at'] = datetime.now().isoformat()
            instance.metadata['svg_version'] = 'v1'

            instance.save(update_fields=['metadata'])
        except Exception as e:
            # SVG 生成失败不影响卡片保存
            print(f"SVG generation failed for card {instance.id}: {e}")

    def create(self, validated_data):
        """创建卡片时自动生成 SVG"""
        instance = super().create(validated_data)
        self._generate_and_attach_svg(instance)
        return instance

    def update(self, instance, validated_data):
        """更新卡片时重新生成 SVG"""
        instance = super().update(instance, validated_data)
        self._generate_and_attach_svg(instance)
        return instance


class CardListSerializer(serializers.ModelSerializer):
    """卡片列表序列化器（简化版，包含复习所需的 metadata）"""
    deck_name = serializers.CharField(source='deck.name', read_only=True)
    card_type_display = serializers.CharField(source='get_card_type_display', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Card
        fields = ('id', 'word', 'card_type', 'card_type_display', 'state',
                  'state_display', 'deck', 'deck_name', 'ef', 'interval',
                  'lapses', 'due_at', 'created_at', 'metadata', 'notes', 'tags')


class ReviewLogSerializer(serializers.ModelSerializer):
    """复习记录序列化器"""
    card_word = serializers.CharField(source='card.word', read_only=True)
    quality_display = serializers.CharField(source='get_quality_display', read_only=True)

    class Meta:
        model = ReviewLog
        fields = '__all__'
        read_only_fields = ('id', 'user', 'reviewed_at')


class CardImportSerializer(serializers.Serializer):
    """卡片导入序列化器"""
    file = serializers.FileField(required=True, help_text='CSV 或 JSON 文件')
    format = serializers.ChoiceField(
        choices=['csv', 'json'],
        required=True,
        help_text='文件格式'
    )
    deck_id = serializers.IntegerField(required=True, help_text='目标卡组ID')
    card_type = serializers.ChoiceField(
        choices=['en', 'zh'],
        default='en',
        help_text='卡片类型'
    )
    conflict_strategy = serializers.ChoiceField(
        choices=['skip', 'overwrite', 'merge'],
        default='skip',
        help_text='冲突处理策略'
    )

    def validate_deck_id(self, value):
        """验证卡组是否存在且属于当前用户"""
        user = self.context.get('request').user
        try:
            deck = Deck.objects.get(id=value, user=user)
        except Deck.DoesNotExist:
            raise serializers.ValidationError('卡组不存在或无权访问')
        return value

    def validate_file(self, value):
        """验证文件大小和类型"""
        # 限制文件大小为 10MB
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('文件大小不能超过 10MB')
        return value


class CardExportSerializer(serializers.Serializer):
    """卡片导出序列化器"""
    format = serializers.ChoiceField(
        choices=['csv', 'json'],
        default='csv',
        help_text='导出格式'
    )
    deck_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text='卡组ID（可选，不指定则导出所有）'
    )


class AIConfigSerializer(serializers.ModelSerializer):
    """AI配置序列化器"""
    api_key = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='API Key (仅写入，不会返回)'
    )
    has_api_key = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = AIConfig
        fields = (
            'id', 'provider', 'base_url', 'model_name', 'api_key',
            'has_api_key', 'enabled', 'auto_summarize',
            'temperature', 'max_tokens', 'custom_chinese_prompt',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'has_api_key')

    def get_has_api_key(self, obj):
        """返回是否已配置API Key（不返回具体内容）"""
        return bool(obj.encrypted_api_key)

    def create(self, validated_data):
        api_key = validated_data.pop('api_key', None)
        user = self.context['request'].user

        # 创建配置
        config = AIConfig.objects.create(user=user, **validated_data)

        # 设置API Key
        if api_key:
            config.set_api_key(api_key)
            config.save()

        return config

    def update(self, instance, validated_data):
        api_key = validated_data.pop('api_key', None)

        # 更新其他字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # 更新API Key（如果提供）
        if api_key is not None:
            instance.set_api_key(api_key)

        instance.save()
        return instance


class AISummarizeRequestSerializer(serializers.Serializer):
    """AI总结请求序列化器"""
    word = serializers.CharField(required=True, help_text='要总结的单词/汉字')
    card_type = serializers.ChoiceField(
        choices=['en', 'zh'],
        required=True,
        help_text='卡片类型'
    )
    context = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='额外上下文信息'
    )
