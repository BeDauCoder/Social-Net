from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from social_network.web_social.models import UserProfile


class Command(BaseCommand):
    help = 'Xóa tài khoản đã yêu cầu xóa từ 30 ngày trước và không đăng nhập lại'

    def handle(self, *args, **kwargs):
        threshold_date = timezone.now() - timedelta(days=30)
        profiles_to_delete = UserProfile.objects.filter(
            deletion_requested_at__lte=threshold_date,
            user__last_login__lte=threshold_date
        )

        for profile in profiles_to_delete:
            user = profile.user
            profile.delete()  # Xóa hồ sơ
            user.delete()  # Xóa tài khoản người dùng
            self.stdout.write(f"Deleted account for user {user.username}")
