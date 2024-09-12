import requests
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model
from urllib.parse import parse_qs
from channels.auth import AuthMiddlewareStack

User = get_user_model()

@database_sync_to_async
def get_user(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return AnonymousUser()

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope['query_string'].decode()
        query_params = parse_qs(query_string)
        token = query_params.get('token', None)
        
        if token:
            token_str = token[0]
            if token_str.startswith('Bearer '):
                token_str = token_str[7:] 
            
            try:
                response = requests.get(
                    'https://api.evtop.ir/api/app/auth/checkAuth',
                    headers={'Authorization': f'Bearer {token_str}'}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    user_id = data['content']['user']['_id']
                    scope['user'] = await get_user(user_id)
                else:
                    scope['user'] = AnonymousUser()
            except (InvalidToken, TokenError) as e:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()

        return await self.inner(scope, receive, send)

def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))