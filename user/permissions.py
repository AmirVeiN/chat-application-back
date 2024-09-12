from rest_framework.permissions import BasePermission
import requests

class ExternalAuthPermission(BasePermission):
    def has_permission(self, request, view):
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return False

        # ارسال درخواست به سرور خارجی برای بررسی توکن
        response = requests.get(
            'https://api.evtop.ir/api/app/auth/checkAuth',
            headers={'Authorization': auth_header}
        )

        if response.status_code != 200:
            return False

        data = response.json()
        request.user = data['content']['user']
        return data.get('success', False)