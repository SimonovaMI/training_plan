"""
Задание глобальных ссылок приложения
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('training_plan/', include('training_plan.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
]
