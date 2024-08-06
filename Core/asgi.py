import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Core.settings")

django_asgi_app = get_asgi_application()

from chat import routing
from Core.middleware import TokenAuthMiddlewareStack

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": TokenAuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        ),
    }
)
