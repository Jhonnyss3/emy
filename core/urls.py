"""
URL configuration for core project.
"""
from django.contrib import admin
from django.urls import include, path

from finances import views as finances_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/register/", finances_views.register, name="register"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("finances.urls")),
]
