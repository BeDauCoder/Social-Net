from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("register/", views.register, name='register'),
    path("", views.login_user, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("home/", views.home, name="home"),
    path("addpost/",views.add_post,name="addpost"),
    path("home/", views.home, name="home"),
    path('home/like/<int:pk>/', views.like_post, name='like_post'),
    path('profile/', views.profile, name='profile'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('friends/<int:user_id>/', views.list_friends, name='list_friends'),
    path('add_friend/<int:user_id>/', views.add_friend, name='add_friend'),
    path('unfriend/<int:user_id>/<int:friend_id>/', views.unfriend, name='unfriend'),  # Đường dẫn hủy kết bạn
    path('accept_friend_request/<int:user_id>/<int:friend_id>/', views.accept_friend_request,
         name='accept_friend_request'),
    path('reject_friend_request/<int:user_id>/<int:friend_id>/', views.reject_friend_request,
         name='reject_friend_request'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)