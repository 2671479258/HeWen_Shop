import re

from django.http import JsonResponse
from users.models import User

class CookieAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 检查请求是否为登录请求
        if request.path == '/login/':
            return self.get_response(request)
        if re.match(r'^/list/\d+/skus/', request.path):
            return self.get_response(request)


        mobile = request.COOKIES.get('mobile')
        if mobile:
            try:
                user = User.objects.get(mobile=mobile)
                request.user = user
            except User.DoesNotExist:
                return JsonResponse({'detail': 'Unauthorized'}, status=401)
        else:
            return JsonResponse({'detail': 'Unauthorized'}, status=401)

        response = self.get_response(request)
        return response