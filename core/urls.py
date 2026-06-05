"""
URL configuration for core project.
"""
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path, re_path
from django.views.static import serve

from finances import views as finances_views
from finances.forms import EmailAuthenticationForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/register/", finances_views.register, name="register"),
    # Override the login view so the e-mail is matched case-insensitively.
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(authentication_form=EmailAuthenticationForm),
        name="login",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path("", include("finances.urls")),
    # Serve user-uploaded media. WhiteNoise only serves static files, and
    # Django's static() helper is a no-op when DEBUG is False, so route it here.
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
