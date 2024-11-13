from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    card_image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    hometown = models.CharField(max_length=100, null=True, blank=True)
    deletion_requested_at = models.DateTimeField(null=True, blank=True)  # Thời gian yêu cầu xóa tài khoản

    def request_account_deletion(self):
        self.deletion_requested_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.user.username}'s Profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

class Group(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(User, through='GroupMember')

    def __str__(self):
        return self.name

class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)


class Page(models.Model):
    title = models.CharField(max_length=255)
    content_html = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pages')
    cover_image = models.ImageField(upload_to='pages/covers/', null=True, blank=True)
    avatar_image = models.ImageField(upload_to='pages/avatars/', null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Post(models.Model):
    PRIVACY_CHOICES = [
        ('public', 'Công khai'),
        ('friends', 'Bạn bè'),
        ('private', 'Chỉ mình tôi'),
        ('blocked', 'Blocked'),
    ]
    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name='posts',null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True)
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public')
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    # Thêm trường mới để chỉ định tường của ai (có thể là bạn bè hoặc bản thân)
    posted_on_wall = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wall_posts", null=True, blank=True)
    def __str__(self):
        return self.content[:20]

    def total_likes(self):
        return self.likes.count()

class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    post = models.ForeignKey('Post', related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    # Trường lưu những người dùng đã like
    likes = models.ManyToManyField(User, related_name='liked_comments', blank=True)

    # Trường cha để xác định comment gốc
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    def __str__(self):
        return self.text[:20]

    def is_reply(self):
        return self.parent is not None

    def total_likes_comment(self):
        return self.likes.count()


class Share(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    shared_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} shared {self.post.title}"


class Follower(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'following')

class FriendRequest(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_requests')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_requests')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('sender', 'receiver')


class Friend(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_user')
    friend = models.ForeignKey(User, on_delete=models.CASCADE, related_name='friend_friend')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')  # Trạng thái kết bạn
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'friend')

    def __str__(self):
        return f'{self.user.username} -> {self.friend.username} ({self.status})'


class Block(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_blocks')
    blocked_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blocked_users')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'blocked_user')

    def __str__(self):
        return f'{self.user.username} has blocked {self.blocked_user.username}'




