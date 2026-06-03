from .models import Household
from .views import get_active_household


def scope(request):
    """Expose the active scope and the user's groups to every template."""
    if not request.user.is_authenticated:
        return {}
    return {
        "active_household": get_active_household(request),
        "user_households": Household.objects.for_user(request.user),
    }
