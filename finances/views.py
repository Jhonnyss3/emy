from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CategoryForm, TransactionForm
from .models import Category, Transaction, TransactionType


def register(request):
    """Sign up a new user and log them straight in."""
    if request.user.is_authenticated:
        return redirect("finances:dashboard")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome! Your account is ready.")
            return redirect("finances:dashboard")
    else:
        form = UserCreationForm()
    return render(request, "registration/register.html", {"form": form})


@login_required
def dashboard(request):
    """Show a summary of the current month plus the latest transactions."""
    today = timezone.localdate()
    month_qs = Transaction.objects.filter(
        user=request.user,
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
        "recent": Transaction.objects.filter(user=request.user).select_related(
            "category"
        )[:10],
    }
    return render(request, "finances/dashboard.html", context)


@login_required
def transaction_list(request):
    """List the user's transactions, optionally filtered by type."""
    transactions = Transaction.objects.filter(user=request.user).select_related(
        "category"
    )
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
    if request.method == "POST":
        form = TransactionForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction created.")
            return redirect("finances:transaction_list")
    else:
        form = TransactionForm(user=request.user)
    return render(
        request,
        "finances/transaction_form.html",
        {"form": form, "title": "New transaction"},
    )


@login_required
def transaction_update(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
    if request.method == "POST":
        form = TransactionForm(
            request.POST, instance=transaction, user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Transaction updated.")
            return redirect("finances:transaction_list")
    else:
        form = TransactionForm(instance=transaction, user=request.user)
    return render(
        request,
        "finances/transaction_form.html",
        {"form": form, "title": "Edit transaction"},
    )


@login_required
def transaction_delete(request, pk):
    transaction = get_object_or_404(Transaction, pk=pk, user=request.user)
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
    categories = Category.objects.filter(user=request.user)
    return render(
        request, "finances/category_list.html", {"categories": categories}
    )


@login_required
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = request.user
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
    category = get_object_or_404(Category, pk=pk, user=request.user)
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
    category = get_object_or_404(Category, pk=pk, user=request.user)
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
