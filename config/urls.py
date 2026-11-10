from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path(settings.ADMIN_URL, admin.site.urls),
    path('conta/', include('apps.accounts.urls')),
    path('resolver/', include('apps.sistemas.urls')),
    path('', include('apps.site.urls')),
]
