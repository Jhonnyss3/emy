from django.utils import timezone

from .forms import RecurringTransactionForm, TransactionForm
from .models import Household
from .views import get_active_household


def scope(request):
    """Expose the active scope and the user's groups to every template."""
    if not request.user.is_authenticated:
        return {}
    household = get_active_household(request)
    return {
        "active_household": household,
        "user_households": Household.objects.for_user(request.user),
        # Unbound forms for the global launch modal (rendered in base.html).
        "launch_transaction_form": TransactionForm(
            user=request.user,
            household=household,
            initial={"date": timezone.localdate()},
        ),
        "launch_recurring_form": RecurringTransactionForm(
            user=request.user,
            household=household,
            initial={"start_date": timezone.localdate()},
        ),
    }
