from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    card_image = models.ImageField(upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    hometown = models.CharField(max_length=100, null=True, blank=True)
    deletion_requested_at = models.DateTimeField(null=True, blank=True)  # Thời gian yêu cầu xóa tài khoản
    bio = models.TextField(null=True, blank=True)  # Thông tin cá nhân
    status = models.CharField(max_length=255, null=True, blank=True)  # Trạng thái ngắn

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
    PUBLIC = 'public'
    PRIVATE = 'private'

    GROUP_TYPE_CHOICES = [
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='group_covers/', blank=True, null=True)  # Ảnh bìa của nhóm
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,)  # Thời gian cập nhật lần cuối
    creator = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)
    members = models.ManyToManyField(User, through='GroupMember',related_name='member_groups')  # Các thành viên của nhóm
    type = models.CharField(max_length=7, choices=GROUP_TYPE_CHOICES, default=PUBLIC)  # Công khai hoặc Riêng tư

    def __str__(self):
        return self.name

    def member_count(self):
        return self.members.count()  # Trả về số lượng thành viên của nhóm

    def get_all_images(self):
        images = []
        for post in self.posts.all():  # Accessing all posts related to the group
            images.extend(post.images.all())  # Assuming 'images' is a related manager in 'PostPage'
        return images


class GroupMember(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE,blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE,blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)


class Page(models.Model):
    title = models.CharField(max_length=255)
    content_html = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pages')
    cover_image = models.ImageField(upload_to='pages/covers/', null=True, blank=True)
    avatar_image = models.ImageField(upload_to='pages/avatars/', null=True, blank=True)
    views = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    editors = models.ManyToManyField(User, related_name='editable_pages', blank=True,null=True)
    likes = models.ManyToManyField(User, related_name='liked_pages', blank=True)

    def __str__(self):
        return self.title

    def total_likes(self):
        return self.likes.count()


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
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True,related_name='posts')
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


class Tag(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='tags')
    tagged_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tagged_posts')
    approved = models.BooleanField(default=False)  # Trạng thái xác nhận

    def __str__(self):
        return f"{self.tagged_user.username} tagged in {self.post.content[:20]}"


class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_recalled = models.BooleanField(default=False)
    is_recalled_by_sender = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.content[:20]}"

class MembershipRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)




