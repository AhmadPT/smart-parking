from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth.views import LoginView, LogoutView
from core.api import api_parking_status

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('vehicles/', include('vehicles.urls')),
    path('access/', include('access.urls')),
    path('detection/', include('detection.urls')),
    path('accounts/login/', LoginView.as_view(template_name='core/login.html'), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('api/status/', api_parking_status, name='api_status'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
