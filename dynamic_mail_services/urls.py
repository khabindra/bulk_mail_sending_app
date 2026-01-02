
from django.contrib import admin
from django.urls import path, include
from .test import test_send_email

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('client.urls')),
    path('api/users/', include('users.urls')),
    path('api/mailings/',include('mailings.urls')),
    path('api/templates/',include('templates.urls')),
    
    # Testing the mail 
    path('api/send-mail-test/',view=test_send_email,name='testing'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
