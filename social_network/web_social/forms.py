from django import forms
from .models import Post,Comment,Tag
from django_summernote.widgets import SummernoteWidget
from django.contrib.auth.models import User
from .models import UserProfile,GroupMember,Group
class PostForm(forms.ModelForm):
    tagged_users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),  # Lọc danh sách người dùng nếu cần
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Gắn thẻ người dùng"
    )
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

    def save(self, commit=True):
        post = super().save(commit=False)
        if commit:
            post.save()
            # Lưu thông tin gắn thẻ
            tagged_users = self.cleaned_data.get('tagged_users', [])
            for user in tagged_users:
                Tag.objects.create(post=post, tagged_user=user)
        return post



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
        fields = ['card_image','avatar', 'date_of_birth', 'hometown','bio','status']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']



class PagePostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']  # Chỉ bao gồm các trường cần thiết
        widgets = {
            'content': SummernoteWidget(attrs={'class': 'form-control'}),
        }



class GroupCoverImageForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['cover_image']


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name', 'description', 'type']

        widgets = {
            'type': forms.Select(attrs={'class': 'form-select'}),
        }


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add any custom initialization or styling (e.g., placeholder)
        self.fields['name'].widget.attrs.update({'placeholder': 'Nhập tên nhóm'})
        self.fields['description'].widget.attrs.update({'placeholder': 'Nhập mô tả nhóm'})

    # Optional: Custom validation for fields
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise forms.ValidationError('Tên nhóm không được để trống.')
        return name

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError('Mô tả nhóm không được để trống.')
        return description