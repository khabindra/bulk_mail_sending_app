

from django.urls import path
from . import views
urlpatterns = [
   path('mail-history/',views.ClientMailHistoryAPIView.as_view(),name='mail-history'), # for getting the client mail
   path('client/', views.ClientDetailAPIView.as_view(), name='client-detail'),  # for get update and delete
]

