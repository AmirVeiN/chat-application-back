import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.wsgi import get_wsgi_application
from channels.auth import AuthMiddlewareStack

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Core.settings")

django_wsgi_app = get_wsgi_application()

from chat import routing
from Core.middleware import TokenAuthMiddlewareStack

application = ProtocolTypeRouter(
    {
        "http": django_wsgi_app,
        "websocket": TokenAuthMiddlewareStack(
            URLRouter(
                routing.websocket_urlpatterns
            )
        ),
    }
)
