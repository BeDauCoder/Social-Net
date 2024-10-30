from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import render, redirect,get_object_or_404
from .forms import PostForm,CommentForm,UserForm,UserProfileForm
from .models import Post, Like, Comment,Friend
from django.db import models
from django.contrib.auth.decorators import login_required
from .models import UserProfile
from django.http import JsonResponse



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

    context = {
        'user': user,
        'posts': posts,
        'likes': likes,
        'comments': comments,
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



