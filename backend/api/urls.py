from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AnnotationViewSet,
    MessageViewSet,
    PDFViewSet,
    UserViewSet,
    WorkspaceViewSet,
)


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'workspaces', WorkspaceViewSet)
router.register(r'pdfs', PDFViewSet)
router.register(r'annotations', AnnotationViewSet)
router.register(r'messages', MessageViewSet)


urlpatterns = [
    path('', include(router.urls)),
]

