from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(
        r'ws/threads/workspace/(?P<workspace_id>\d+)/pdf/(?P<pdf_id>\d+)/$',
        consumers.ThreadConsumer.as_asgi()
    ),
]

