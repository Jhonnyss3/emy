from django.shortcuts import redirect
from django.urls import reverse


class ProfileCompletionMiddleware:
    """Force authenticated users without a profile to complete it first."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.path.startswith(
            "/admin/"
        ):
            profile_url = reverse("finances:profile_edit")
            allowed = (profile_url, reverse("logout"))
            if request.path not in allowed and not hasattr(
                request.user, "profile"
            ):
                return redirect(profile_url)
        return self.get_response(request)
