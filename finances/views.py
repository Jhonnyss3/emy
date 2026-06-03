from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CategoryForm,
    HouseholdForm,
    MemberAddForm,
    ProfileForm,
    RegistrationForm,
    TransactionForm,
)
from .models import (
    Category,
    Household,
    HouseholdMembership,
    Transaction,
    TransactionType,
)


def get_active_household(request):
    """Resolve the active scope: a Household the user belongs to, or None (personal)."""
    household_id = request.session.get("active_household_id")
    if not household_id:
        return None
    return (
        Household.objects.for_user(request.user).filter(pk=household_id).first()
    )


@login_required
def scope_switch(request):
    """Switch the active scope between personal and one of the user's groups."""
    if request.method == "POST":
        scope = request.POST.get("scope", "personal")
        if scope == "personal":
            request.session.pop("active_household_id", None)
            messages.success(request, "Escopo alterado para Pessoal.")
        elif scope.isdigit():
            household = (
                Household.objects.for_user(request.user).filter(pk=scope).first()
            )
            if household:
                request.session["active_household_id"] = household.pk
                messages.success(
                    request, f"Escopo alterado para {household.name}."
                )
            else:
                messages.error(request, "Grupo inválido.")
        return redirect("finances:dashboard")

    return render(
        request,
        "finances/scope_switch.html",
        {"households": Household.objects.for_user(request.user)},
    )


@login_required
def household_list(request):
    """List the groups the user belongs to."""
    return render(
        request,
        "finances/household_list.html",
        {"households": Household.objects.for_user(request.user)},
    )


@login_required
def household_create(request):
    if request.method == "POST":
        form = HouseholdForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                household = form.save(commit=False)
                household.created_by = request.user
                household.save()
                HouseholdMembership.objects.create(
                    household=household, user=request.user
                )
            messages.success(request, "Grupo criado.")
            return redirect("finances:household_detail", pk=household.pk)
    else:
        form = HouseholdForm()
    return render(
        request,
        "finances/household_form.html",
        {"form": form, "title": "Novo grupo"},
    )


@login_required
def household_detail(request, pk):
    household = get_object_or_404(
        Household.objects.for_user(request.user), pk=pk
    )
    return render(
        request,
        "finances/household_detail.html",
        {
            "household": household,
            "memberships": household.memberships.select_related("user"),
            "is_owner": household.created_by_id == request.user.id,
            "form": MemberAddForm(),
        },
    )


@login_required
def member_add(request, pk):
    household = get_object_or_404(
        Household.objects.for_user(request.user), pk=pk
    )
    if household.created_by_id != request.user.id:
        messages.error(request, "Apenas o dono do grupo pode adicionar membros.")
        return redirect("finances:household_detail", pk=pk)

    if request.method == "POST":
        form = MemberAddForm(request.POST)
        if form.is_valid():
            if HouseholdMembership.objects.filter(
                household=household, user=form.user
            ).exists():
                messages.error(request, "Essa pessoa já faz parte do grupo.")
            else:
                HouseholdMembership.objects.create(
                    household=household, user=form.user
                )
                messages.success(request, "Membro adicionado.")
            return redirect("finances:household_detail", pk=pk)
        return render(
            request,
            "finances/household_detail.html",
            {
                "household": household,
                "memberships": household.memberships.select_related("user"),
                "is_owner": True,
                "form": form,
            },
        )
    return redirect("finances:household_detail", pk=pk)


@login_required
def member_remove(request, pk, user_id):
    household = get_object_or_404(
        Household.objects.for_user(request.user), pk=pk
    )
    if household.created_by_id != request.user.id:
        messages.error(request, "Apenas o dono do grupo pode remover membros.")
        return redirect("finances:household_detail", pk=pk)

    if request.method == "POST":
        if user_id == household.created_by_id:
            messages.error(request, "O dono não pode ser removido.")
        else:
            HouseholdMembership.objects.filter(
                household=household, user_id=user_id
            ).delete()
            messages.success(request, "Membro removido.")
    return redirect("finances:household_detail", pk=pk)


def register(request):
    """Sign up a new user and log them straight in."""
    if request.user.is_authenticated:
        return redirect("finances:dashboard")
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Conta criada! Complete seu perfil.")
            return redirect("finances:profile_edit")
    else:
        form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def profile_edit(request):
    """Edit the current user's profile; also runs right after sign-up."""
    profile = getattr(request.user, "profile", None)
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado.")
            return redirect("finances:dashboard")
    else:
        form = ProfileForm(instance=profile, user=request.user)
    return render(request, "finances/profile_form.html", {"form": form})


@login_required
def dashboard(request):
    """Show a summary of the current month plus the latest transactions."""
    household = get_active_household(request)
    today = timezone.localdate()
    month_qs = Transaction.objects.in_scope(request.user, household).filter(
        date__year=today.year,
        date__month=today.month,
    )

    income = month_qs.filter(type=TransactionType.INCOME).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")
    expense = month_qs.filter(type=TransactionType.EXPENSE).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    context = {
        "today": today,
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "recent": Transaction.objects.in_scope(request.user, household)
        .select_related("category")[:10],
    }
    return render(request, "finances/dashboard.html", context)


@login_required
def transaction_list(request):
    """List the transactions in the active scope, optionally filtered by type."""
    household = get_active_household(request)
    transactions = Transaction.objects.in_scope(
        request.user, household
    ).select_related("category")
    type_filter = request.GET.get("type")
    if type_filter in TransactionType.values:
        transactions = transactions.filter(type=type_filter)

    return render(
        request,
        "finances/transaction_list.html",
        {"transactions": transactions, "type_filter": type_filter},
    )


@login_required
def transaction_create(request):
    household = get_active_household(request)
    if request.method == "POST":
        form = TransactionForm(
            request.POST, user=request.user, household=household
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction created.")
            return redirect("finances:transaction_list")
    else:
        form = TransactionForm(user=request.user, household=household)
    return render(
        request,
        "finances/transaction_form.html",
        {"form": form, "title": "New transaction"},
    )


@login_required
def transaction_update(request, pk):
    household = get_active_household(request)
    transaction = get_object_or_404(
        Transaction.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        form = TransactionForm(
            request.POST,
            instance=transaction,
            user=request.user,
            household=household,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction updated.")
            return redirect("finances:transaction_list")
    else:
        form = TransactionForm(
            instance=transaction, user=request.user, household=household
        )
    return render(
        request,
        "finances/transaction_form.html",
        {"form": form, "title": "Edit transaction"},
    )


@login_required
def transaction_delete(request, pk):
    household = get_active_household(request)
    transaction = get_object_or_404(
        Transaction.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        transaction.delete()
        messages.success(request, "Transaction deleted.")
        return redirect("finances:transaction_list")
    return render(
        request,
        "finances/confirm_delete.html",
        {"object": transaction, "title": "Delete transaction"},
    )


@login_required
def category_list(request):
    household = get_active_household(request)
    categories = Category.objects.in_scope(request.user, household)
    return render(
        request, "finances/category_list.html", {"categories": categories}
    )


@login_required
def category_create(request):
    household = get_active_household(request)
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
            category.household = household
            category.save()
            messages.success(request, "Category created.")
            return redirect("finances:category_list")
    else:
        form = CategoryForm()
    return render(
        request,
        "finances/category_form.html",
        {"form": form, "title": "New category"},
    )


@login_required
def category_update(request, pk):
    household = get_active_household(request)
    category = get_object_or_404(
        Category.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, "Category updated.")
            return redirect("finances:category_list")
    else:
        form = CategoryForm(instance=category)
    return render(
        request,
        "finances/category_form.html",
        {"form": form, "title": "Edit category"},
    )


@login_required
def category_delete(request, pk):
    household = get_active_household(request)
    category = get_object_or_404(
        Category.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        if category.transactions.exists():
            messages.error(
                request,
                "This category still has transactions and cannot be deleted.",
            )
            return redirect("finances:category_list")
        category.delete()
        messages.success(request, "Category deleted.")
        return redirect("finances:category_list")
    return render(
        request,
        "finances/confirm_delete.html",
        {"object": category, "title": "Delete category"},
    )
