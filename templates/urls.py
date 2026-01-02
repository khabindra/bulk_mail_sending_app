from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MailTypeListView,
    MailTypeDetailView,
    EmailTemplateViewSet,
    InlineImageViewSet
)

# Create a router and register our ViewSets with it.
router = DefaultRouter()
# basename is required because our queryset uses select_related which can confuse DRF sometimes
router.register(r'templates', EmailTemplateViewSet, basename='emailtemplate')
router.register(r'images', InlineImageViewSet, basename='inlineimage')

urlpatterns = [
    # URL for MailType List and Detail
    path('types/', MailTypeListView.as_view(), name='mail-type-list'),
    path('types/<int:pk>/', MailTypeDetailView.as_view(), name='mail-type-detail'),
    
    # Include the router URLs (handles templates and images)
    path('', include(router.urls)),
]