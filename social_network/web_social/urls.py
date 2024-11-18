# urls.py
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommentViewSet
from django.urls import path
from .consumers import ChatConsumer

router = DefaultRouter()
router.register(r'comments', CommentViewSet)



urlpatterns = [
    # User-related URLs
    path("register/", views.register, name='register'),
    path("", views.login_user, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path('delete_account/', views.delete_account, name='delete_account'),

    # Home and post URLs
    path("home/", views.home, name="home"),
    path("addpost/", views.add_post, name="addpost"),
    path('home/like/<int:pk>/', views.like_post, name='like_post'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/<int:pk>/add_comment/', views.add_comment, name='add_comment'),  # Add comment URL


    # Profile-related URLs
    path('profile/<int:user_id>/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),

    # Friend management URLs
    path('friends/<int:user_id>/', views.list_friends, name='list_friends'),
    path('add_friend/<int:user_id>/', views.add_friend, name='add_friend'),
    path('friends/<int:user_id>/block/<int:friend_id>/', views.block_friend, name='block_friend'),
    path('friends/<int:user_id>/unblock/<int:friend_id>/', views.unblock_friend, name='unblock_friend'),
    path('unfriend/<int:user_id>/<int:friend_id>/', views.unfriend, name='unfriend'),
    path('accept_friend_request/<int:user_id>/<int:friend_id>/', views.accept_friend_request,
         name='accept_friend_request'),
    path('reject_friend_request/<int:user_id>/<int:friend_id>/', views.reject_friend_request,
         name='reject_friend_request'),
    path('following/', views.following_list, name='following_list'),
    path('follow/<int:user_id>/', views.follow_user, name='follow_user'),
    path('unfollow/<int:user_id>/', views.unfollow_user, name='unfollow_user'),
    path('suggested_friends/', views.suggested_friends, name='suggested_friends'),
    path('send_friend_request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('list_friends/<int:user_id>/', views.list_friends, name='list_friends'),


    # Include the API router for ViewSets
    path('', include(router.urls)),
    path('chat/<int:user_id>/', views.chat_view, name='chat'),

    #manager page
    path('page_manager/', views.PageListView.as_view(), name='page_list'),
    path('page_manager/new/', views.PageCreateView.as_view(), name='page_create'),
    path('page_manager/<int:pk>/edit/', views.PageUpdateView.as_view(), name='page_edit'),
    path('page_manager/<int:pk>/delete/', views.PageDeleteView.as_view(), name='page_delete'),
    path('pages/', views.page_list_user, name='page_list_user'),  # Đường dẫn cho danh sách trang
    path('pages/<int:pk>/', views.page_detail_user, name='page_detail'),  # Đường dẫn cho chi tiết từng trang
    path('page/<int:page_id>/add-post/', views.PagePostCreateView.as_view(), name='page_post_create'),
    # Sửa bài viết
    path('post/<int:pk>/edit/', views.PostPostUpdateView.as_view(), name='post_edit'),

    # Xóa bài viết
    path('post/<int:post_id>/delete/', views.PostPostDeleteView, name='post_delete'),
    path('manage-editors/<int:page_id>/', views.manage_editors, name='manage_editors'),


    #manager post
    path('my_posts/', views.UserPostListView.as_view(), name='user_post_list'),
    path('my_posts/new/', views.PostCreateView.as_view(), name='post_create'),
    path('my_posts/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    path('my_posts/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('share/<int:post_id>/', views.share_post, name='share_post'),
    path('post/delete/<int:post_id>/', views.delete_post, name='delete_post'),
    path('tag/approve/<int:tag_id>/', views.approve_tag, name='approve_tag'),
    path('tag/remove/<int:tag_id>/', views.remove_tag, name='remove_tag'),

    path('search/', views.search_view, name='search_view'),

]

# Static and media file serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
