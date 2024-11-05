from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Nếu là yêu cầu GET, HEAD, hoặc OPTIONS, cho phép truy cập
        if request.method in SAFE_METHODS:
            return True
        # Nếu là action 'reply', không cần kiểm tra quyền sở hữu
        if view.action == 'reply':
            return True
        # Kiểm tra quyền sở hữu cho các yêu cầu khác (PUT, DELETE)
        return obj.user == request.user


class MyProtectedView(APIView):
    permission_classes = [IsAuthenticated]  # Chỉ cho phép người dùng đã đăng nhập

    def get(self, request):
        return Response({"message": "Hello, authenticated user!"})
