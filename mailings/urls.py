from django.urls import path
from .views import (
    SenderEmailListCreateView, SenderEmailDetailView,
    MailLogListView, MailLogDetailView,
    AdminBulkMailWithInlineImageAPIView,
    EmailPreviewAPIView
)

app_name = 'mailings'

urlpatterns = [
   # Sender Email Endpoints
   path('senders/', SenderEmailListCreateView.as_view(), name='sender-list-create'),
   path('senders/<int:pk>/', SenderEmailDetailView.as_view(), name='sender-detail'),

   # Mail Log Endpoints
   path('logs/', MailLogListView.as_view(), name='log-list-create'),
   path('logs/<int:pk>/', MailLogDetailView.as_view(), name='log-detail'),

   # admin bulk mail send path
   path('send-mail/',AdminBulkMailWithInlineImageAPIView.as_view(),name='inline-image-mail'),
   path('preview/', EmailPreviewAPIView.as_view(), name='email-preview'),
]