from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import PostForm,CommentForm,UserForm,UserProfileForm
from .models import Post, Like, Comment,Friend
from django.db import models
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.shortcuts import redirect, get_object_or_404, render
from django.views.decorators.http import require_POST
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import CommentSerializer,ReplySerializer
from .permissions import IsOwnerOrReadOnly,IsAuthenticated
from rest_framework import viewsets
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Page


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Tài Khoản đã tồn tại')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email đã được sử dụng')
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.save()
            messages.success(request, 'Tạo Tài Khoản Thành Công')
            return redirect('login')
    return render(request,'register.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Thông tin đăng nhập không hợp lệ')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')


@login_required
def home(request):
    user = request.user
    posts = Post.objects.filter(
        models.Q(privacy='public') |
        models.Q(author=user)
    )
    likes = Like.objects.filter(user=user)
    comments = Comment.objects.filter(user=user)
    friends = Friend.objects.filter(user=user, status='accepted')  # Danh sách bạn bè

    context = {
        'user': user,
        'posts': posts,
        'likes': likes,
        'comments': comments,
        'friends': friends,  # Truyền danh sách bạn bè vào context
    }
    return render(request, 'home.html', context)



def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('home')  # Điều hướng về trang chủ hoặc trang cần thiết
    else:
        form = PostForm()
    return render(request, 'add_post.html', {'form': form})


@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.likes.filter(id=request.user.id).exists():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
    return redirect('home')


@login_required
def edit_profile(request):
    # Tạo UserProfile nếu chưa có
    UserProfile.objects.get_or_create(user=request.user)

    user_form = UserForm(instance=request.user)
    profile_form = UserProfileForm(instance=request.user.userprofile)

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=request.user.userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')  # Chuyển hướng sau khi lưu

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'edit_profile.html', context)


@login_required
def profile(request):
    user = request.user
    user_profile = user.userprofile  # Truy cập vào hồ sơ người dùng

    context = {
        'user': user,
        'user_profile': user_profile,
    }
    return render(request, 'profile.html', context)


# Xem danh sách bạn bè
def list_friends(request, user_id):
    user = get_object_or_404(User, id=user_id)
    friends = Friend.objects.filter(user=user, status='accepted')  # Bạn bè đã được chấp nhận
    pending_friend_requests = Friend.objects.filter(friend=user, status='pending')  # Lời mời đang chờ xử lý

    return render(request, 'list_friends.html', {
        'user': user,
        'friends': friends,
        'pending_friend_requests': pending_friend_requests
    })



# Gửi lời mời kết bạn
def add_friend(request, user_id):
    if request.method == 'POST':
        new_friend_username = request.POST.get('new_friend_username')  # Lấy username từ form POST
        user = get_object_or_404(User, id=user_id)
        friend = get_object_or_404(User, username=new_friend_username)  # Tìm theo username

        # Kiểm tra nếu lời mời kết bạn đã tồn tại
        existing_friendship = Friend.objects.filter(user=user, friend=friend).first()

        if existing_friendship:
            # Nếu lời mời đã tồn tại nhưng bị từ chối, cập nhật thành 'pending'
            if existing_friendship.status == 'rejected':
                existing_friendship.status = 'pending'
                existing_friendship.save()
                return redirect('list_friends', user_id=user_id)
            else:
                # Nếu trạng thái không phải 'rejected', thông báo là lời mời đã tồn tại
                return redirect('list_friends', user_id=user_id)

        # Nếu chưa có mối quan hệ nào, tạo lời mời kết bạn mới
        Friend.objects.create(user=user, friend=friend, status='pending')

        return redirect('list_friends', user_id=user_id)

    return redirect('list_friends', user_id=user_id)



# Chấp nhận lời mời kết bạn
def accept_friend_request(request, user_id, friend_id):
    user = get_object_or_404(User, id=user_id)
    friend_request = get_object_or_404(Friend, user=friend_id, friend=user, status='pending')  # Tìm lời mời

    # Chuyển trạng thái thành "accepted"
    friend_request.status = 'accepted'
    friend_request.save()

    # Tạo mối quan hệ ngược lại giữa hai người
    Friend.objects.create(user=user, friend=friend_request.user, status='accepted')

    return redirect('list_friends', user_id=user_id)

# Từ chối lời mời kết bạn
def reject_friend_request(request, user_id, friend_id):
    user = get_object_or_404(User, id=user_id)
    friend_request = get_object_or_404(Friend, user=friend_id, friend=user, status='pending')  # Tìm lời mời

    # Chuyển trạng thái thành "rejected"
    friend_request.status = 'rejected'
    friend_request.save()

    return redirect('list_friends', user_id=user_id)



# Hủy kết bạn
def unfriend(request, user_id, friend_id):
    user = get_object_or_404(User, id=user_id)
    friend = get_object_or_404(User, id=friend_id)
    # Xóa mối quan hệ bạn bè hai chiều
    Friend.objects.filter(user=user, friend=friend).delete()
    Friend.objects.filter(user=friend, friend=user).delete()

    return redirect('list_friends', user_id=user_id)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsOwnerOrReadOnly]

    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        comment = self.get_object()
        user = request.user
        if user in comment.likes.all():
            comment.likes.remove(user)
            return Response({'status': 'unliked'}, status=status.HTTP_200_OK)
        else:
            comment.likes.add(user)
            return Response({'status': 'liked'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reply(self, request, pk=None):
        comment = self.get_object()  # Bình luận mà bạn sẽ reply
        serializer = ReplySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, post=comment.post, parent=comment)  # Gán parent và post
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], permission_classes=[IsAuthenticated])
    def delete_comment(self, request, pk=None):
        comment = self.get_object()
        if comment.user == request.user:  # Kiểm tra quyền sở hữu
            comment.delete()
            return Response({'status': 'deleted'}, status=status.HTTP_204_NO_CONTENT)
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=True, methods=['put'], permission_classes=[IsAuthenticated])
    def update_comment(self, request, pk=None):
        comment = self.get_object()  # Lấy bình luận dựa trên `pk`

        # Kiểm tra quyền sở hữu
        if comment.user != request.user:
            return Response({'error': 'Bạn không có quyền sửa bình luận này'}, status=status.HTTP_403_FORBIDDEN)

        # Thực hiện cập nhật bình luận
        serializer = self.get_serializer(comment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all()  # Lấy tất cả các bình luận của bài viết này
    form = CommentForm()  # Tạo form cho bình luận

    return render(request, 'post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form,  # Truyền form vào context
    })



@require_POST  # Chỉ cho phép yêu cầu POST để tránh lỗi phương thức không hợp lệ
def add_comment(request, pk):
    # Lấy bài viết theo pk hoặc trả về 404 nếu không tìm thấy
    post = get_object_or_404(Post, pk=pk)
    form = CommentForm(request.POST)

    if form.is_valid():
        # Tạo đối tượng comment nhưng chưa lưu vào DB
        comment = form.save(commit=False)
        comment.post = post  # Gán bài viết cho bình luận
        comment.user = request.user  # Gán người dùng hiện tại cho bình luận
        comment.save()  # Lưu bình luận vào DB

    # Chuyển hướng về trang chi tiết của bài viết
    return redirect('post_detail', pk=post.pk)

from django.contrib.auth.decorators import login_required

@login_required
def chat_view(request, receiver_id):
    receiver = get_object_or_404(User, id=receiver_id)
    user = request.user

    # Lấy danh sách bạn bè của người dùng hiện tại
    friends = Friend.objects.filter(user=user, status='accepted')

    context = {
        'receiver': receiver,  # Người nhận cụ thể mà bạn đang trò chuyện
        'friends': friends      # Danh sách bạn bè
    }
    return render(request, 'chat.html', context)




class PageListView(LoginRequiredMixin, ListView):
    model = Page
    template_name = 'page_manager/page_list.html'
    context_object_name = 'pages'

class PageCreateView(LoginRequiredMixin, CreateView):
    model = Page
    template_name = 'page_manager/page_form.html'
    fields = ['title', 'content_html', 'cover_image', 'avatar_image']
    success_url = reverse_lazy('page_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PageUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Page
    template_name = 'page_manager/page_form.html'
    fields = ['title', 'content_html', 'cover_image', 'avatar_image']
    success_url = reverse_lazy('page_list')

    def test_func(self):
        page = self.get_object()
        return self.request.user == page.author

class PageDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Page
    template_name = 'page_manager/page_confirm_delete.html'
    success_url = reverse_lazy('page_list')

    def test_func(self):
        page = self.get_object()
        return self.request.user == page.author


def page_list_user(request):
    pages = Page.objects.all()  # Lấy tất cả các trang
    return render(request, 'page_list_user.html', {'pages': pages})

def page_detail_user(request, pk):
    page = get_object_or_404(Page, pk=pk)  # Lấy trang theo khóa chính (primary key)
    return render(request, 'page_detail.html', {'page': page})


# Danh sách bài viết của người dùng trên trang cá nhân
class UserPostListView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'post_manager/user_post_list.html'
    context_object_name = 'posts'

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user).order_by('-created_at')

# Tạo bài viết mới
class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'post_manager/post_form.html'
    success_url = reverse_lazy('user_post_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

# Sửa bài viết
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'post_manager/post_form.html'
    success_url = reverse_lazy('user_post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author

# Xóa bài viết
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'post_manager/post_confirm_delete.html'
    success_url = reverse_lazy('user_post_list')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.author
