from audioop import reverse

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import PostForm,CommentForm,UserForm,UserProfileForm,PostWallForm
from .models import Post, Like, Comment,Friend
from django.db import models
from django.contrib.auth.decorators import login_required
from .models import UserProfile,Share
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
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta


def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        email = request.POST.get('email')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        # Kiểm tra xem người dùng đã tồn tại chưa
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register')

        # Tạo người dùng mới nếu tất cả điều kiện thỏa mãn
        user = User.objects.create_user(username=username, password=password, email=email)
        user.save()

        messages.success(request, "Registration successful! Please login.")
        return redirect('login')

    return render(request, 'register.html')

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


from django.db import models
from django.utils import timezone

@login_required
def home(request):
    user = request.user

    # Lấy danh sách bạn bè
    friends = Friend.objects.filter(user=user, status='accepted').values_list('friend_id', flat=True)

    # Lấy danh sách người mà user đang theo dõi
    following = Follower.objects.filter(user=user).values_list('following_id', flat=True)

    # Lấy danh sách người dùng bị chặn
    blocked_users = Friend.objects.filter(
        models.Q(user=user, status='blocked') | models.Q(friend=user, status='blocked')
    ).values_list('user_id', 'friend_id')
    blocked_user_ids = {blocked_id for blocked_ids in blocked_users for blocked_id in blocked_ids}

    # Xác định kiểu sắp xếp
    ordering = request.GET.get('ordering', 'by_likes')  # mặc định là sắp xếp theo "like"

    # Bộ lọc bài viết dựa trên quyền riêng tư và trạng thái chặn
    posts = Post.objects.filter(
        (models.Q(privacy='public') |
         models.Q(author=user) |
         (models.Q(privacy='friends') & models.Q(author__id__in=friends))
         ) & ~models.Q(author__id__in=blocked_user_ids)
    ).annotate(
        # Tính số lượng "like" cho từng bài viết
        like_count=models.Count('likes'),
        # Gán mức độ ưu tiên cho mỗi bài viết: 1 là bạn bè, 2 là theo dõi, 3 là khác
        priority=models.Case(
            models.When(author__id__in=friends, then=models.Value(1)),
            models.When(author__id__in=following, then=models.Value(2)),
            default=models.Value(3),
            output_field=models.IntegerField()
        )
    )

    if ordering == 'by_likes':
        # Sắp xếp bài viết theo mức độ ưu tiên và sau đó theo số lượng "like" trong từng nhóm
        posts = posts.order_by('priority', '-like_count')
    else:  # chronological
        # Lọc bài viết từ bạn bè và người theo dõi, sắp xếp theo thời gian
        posts = posts.filter(models.Q(author__id__in=friends) | models.Q(author__id__in=following)).order_by('priority', '-created_at')

    # Lấy lượt thích và bình luận của người dùng
    likes = Like.objects.filter(user=user)
    comments = Comment.objects.filter(user=user)

    # Lấy các bài viết đã được chia sẻ bởi bạn bè hoặc chính người dùng
    shared_posts = Share.objects.filter(
        models.Q(user=user) | models.Q(user__id__in=friends)
    ).select_related('post', 'user')

    # Truyền dữ liệu vào context
    context = {
        'user': user,
        'posts': posts,
        'likes': likes,
        'comments': comments,
        'friends': friends,
        'shared_posts': shared_posts,
        'ordering': ordering,
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


from django.shortcuts import redirect

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
            # Chuyển hướng đến trang profile của người dùng
            return redirect('profile', user_id=request.user.id)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'edit_profile.html', context)



from django.db.models import Q

@login_required
def profile(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)  # Người dùng mà ta đang xem hồ sơ
    user_profile = profile_user.userprofile

    # Lấy tất cả bài viết được đăng lên tường của profile_user hoặc do profile_user tự đăng
    wall_posts = Post.objects.filter(
        Q(author=profile_user) | Q(posted_on_wall=profile_user)
    ).order_by('-created_at')

    # Xử lý form đăng bài
    if request.method == 'POST':
        form = PostWallForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.posted_on_wall = profile_user  # Đăng bài lên tường của người dùng đang xem
            post.save()
            return redirect('profile', user_id=profile_user.id)
    else:
        form = PostWallForm()

    context = {
        'profile_user': profile_user,
        'user_profile': user_profile,
        'wall_posts': wall_posts,  # Đảm bảo rằng 'wall_posts' chứa cả bài viết của profile_user và bài đăng trên tường của họ
        'form': form,
    }
    return render(request, 'profile.html', context)







# Xem danh sách bạn bè
def list_friends(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # Lấy danh sách bạn bè đã được chấp nhận và không bị chặn
    friends = Friend.objects.filter(user=user, status='accepted')

    # Lời mời kết bạn đang chờ và không bị chặn
    pending_friend_requests = Friend.objects.filter(friend=user, status='pending').exclude(
        user__in=Friend.objects.filter(status='blocked').values('friend'))

    blocked_friends = Friend.objects.filter(user=user, status='blocked')
    return render(request, 'list_friends.html', {
        'user': user,
        'friends': friends,
        'pending_friend_requests': pending_friend_requests,
        'blocked_friends': blocked_friends
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
        post_author = comment.post.author
        if comment.user == request.user or post_author == request.user:  # Kiểm tra quyền sở hữu
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

# Chặn bạn bè
def block_friend(request, user_id, friend_id):
    user = get_object_or_404(User, id=user_id)
    friend = get_object_or_404(User, id=friend_id)

    # Kiểm tra xem mối quan hệ có tồn tại không
    friendship, created = Friend.objects.get_or_create(user=user, friend=friend)

    # Chuyển trạng thái thành "blocked"
    friendship.status = 'blocked'
    friendship.save()

    # Nếu có quan hệ ngược lại, cũng chuyển thành "blocked"
    Friend.objects.update_or_create(
        user=friend, friend=user,
        defaults={'status': 'blocked'}
    )

    return redirect('list_friends', user_id=user_id)


# Bỏ chặn bạn bè
# Bỏ chặn và thiết lập lại quan hệ bạn bè nếu cần
def unblock_friend(request, user_id, friend_id):
    user = get_object_or_404(User, id=user_id)
    friend = get_object_or_404(User, id=friend_id)

    # Xóa mối quan hệ blocked
    Friend.objects.filter(user=user, friend=friend, status='blocked').delete()
    Friend.objects.filter(user=friend, friend=user, status='blocked').delete()

    # Kiểm tra lại quan hệ bạn bè sau khi bỏ chặn
    existing_friendship = Friend.objects.filter(user=user, friend=friend).first()

    # Nếu chưa có quan hệ "accepted", tạo lại mối quan hệ
    if not existing_friendship:
        Friend.objects.create(user=user, friend=friend, status='accepted')
        Friend.objects.create(user=friend, friend=user, status='accepted')

    return redirect('list_friends', user_id=user_id)



def delete_account(request):
    # Thiết lập thời điểm yêu cầu xóa tài khoản
    user_profile = request.user.userprofile
    user_profile.request_account_deletion()

    # Đăng xuất người dùng và chuyển hướng đến trang đăng nhập
    logout(request)
    return redirect('login')


def account_deleted(request):
    return render(request, 'account_deleted.html')



@login_required
def share_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    # Kiểm tra nếu người dùng hiện tại đã chia sẻ bài viết này chưa
    existing_share = Share.objects.filter(user=request.user, post=post).exists()
    if not existing_share:
        # Tạo bản ghi chia sẻ mới nếu chưa có
        Share.objects.create(user=request.user, post=post)

    return redirect('profile', user_id=post.author.id)  # Quay lại trang cá nhân của người đăng bài

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    # Chỉ cho phép xóa nếu người dùng là tác giả hoặc chủ sở hữu của tường
    if request.user == post.author or request.user == post.posted_on_wall:
        post.delete()
        messages.success(request, 'Bài viết đã được xóa thành công.')
    else:
        messages.error(request, 'Bạn không có quyền xóa bài viết này.')
    return redirect('profile', user_id=post.posted_on_wall.id)



from .models import Follower,FriendRequest

def follow_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if request.user != target_user:
        Follower.objects.get_or_create(user=request.user, following=target_user)
        messages.success(request, f"Bạn đã theo dõi {target_user.username}.")
    return redirect('suggested_friends')




# views.py
from django.db.models import Q

def suggested_friends(request):
    # Loại trừ người dùng hiện tại và tất cả người dùng đã có mối quan hệ kết bạn (bất kỳ trạng thái nào)
    excluded_users = [request.user.id]

    # Lấy tất cả user_id mà request.user đã kết bạn hoặc gửi lời mời (bất kỳ trạng thái nào)
    related_user_ids = Friend.objects.filter(
        Q(user=request.user) | Q(friend=request.user)
    ).values_list('friend', 'user')

    # Thêm tất cả các user_id có trong quan hệ với người dùng hiện tại vào danh sách loại trừ
    excluded_users.extend(list(set([user_id for ids in related_user_ids for user_id in ids])))

    # Lấy danh sách người dùng để gợi ý
    suggested_users = User.objects.exclude(id__in=excluded_users)

    context = {
        'suggested_users': suggested_users
    }
    return render(request, 'suggested_friends.html', context)



def send_friend_request(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if request.user != target_user:
        # Kiểm tra xem đã có mối quan hệ hoặc lời mời kết bạn trước đó hay chưa
        existing_friendship = Friend.objects.filter(user=request.user, friend=target_user).first()

        if existing_friendship:
            # Nếu lời mời đã tồn tại với trạng thái từ chối, cập nhật lại trạng thái thành "pending"
            if existing_friendship.status == 'rejected':
                existing_friendship.status = 'pending'
                existing_friendship.save()
                messages.success(request, f"Đã gửi lại lời mời kết bạn đến {target_user.username}.")
            else:
                # Nếu lời mời đã tồn tại với trạng thái khác, thông báo là lời mời đã tồn tại
                messages.info(request, f"Bạn đã gửi lời mời kết bạn hoặc đã kết bạn với {target_user.username}.")
        else:
            # Nếu chưa có mối quan hệ nào, tạo lời mời kết bạn mới với trạng thái "pending"
            Friend.objects.create(user=request.user, friend=target_user, status='pending')
            messages.success(request, f"Đã gửi lời mời kết bạn đến {target_user.username}.")
    return redirect('suggested_friends')  # Chuyển hướng về trang gợi ý bạn bè




def following_list(request):
    # Những người mà người dùng hiện tại đang theo dõi
    following = Follower.objects.filter(user=request.user)
    # Những người đang theo dõi người dùng hiện tại
    followers = Follower.objects.filter(following=request.user)

    context = {
        'following': following,
        'followers': followers
    }
    return render(request, 'following_list.html', context)

def unfollow_user(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    # Xóa bản ghi theo dõi trong model Follower
    Follower.objects.filter(user=request.user, following=target_user).delete()
    messages.success(request, f"Bạn đã bỏ theo dõi {target_user.username}.")
    return redirect('following_list')  # Điều hướng về trang danh sách theo dõi (hoặc trang mong muốn khác)


