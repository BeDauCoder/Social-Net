from django import forms
from .models import Post,Comment
from django_summernote.widgets import SummernoteWidget
from django.contrib.auth.models import User
from .models import UserProfile
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'group', 'privacy']
        widgets = {
            'content': SummernoteWidget(attrs={'class': 'form-control'}),
            'group': forms.Select(attrs={'class': 'form-control'}),
            'privacy': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'content': 'Nội dung',
            'group': 'Nhóm',
            'privacy': 'Quyền riêng tư',
        }

class PostWallForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'privacy']
        widgets = {
            'content': SummernoteWidget(attrs={'class': 'form-control'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']  # Trường duy nhất cần cho bình luận là text
        widgets = {
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['card_image','avatar', 'date_of_birth', 'hometown']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
