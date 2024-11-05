# your_app/serializers.py
from rest_framework import serializers
from .models import Comment

class CommentSerializer(serializers.ModelSerializer):
    replies = serializers.SerializerMethodField()
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'text', 'created_at', 'likes_count', 'replies', 'parent']

    def get_replies(self, obj):
        return CommentSerializer(obj.replies.all(), many=True).data

# serializers.py
from rest_framework import serializers
from .models import Comment

class ReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['text', 'user', 'post', 'parent']
        extra_kwargs = {
            'user': {'read_only': True},
            'post': {'read_only': True},
            'parent': {'read_only': True},
        }


