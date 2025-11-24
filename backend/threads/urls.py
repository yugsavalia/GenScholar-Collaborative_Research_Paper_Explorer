from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'threads', views.ThreadViewSet, basename='thread')

urlpatterns = [
    path('', include(router.urls)),
]

