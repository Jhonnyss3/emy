import calendar
import uuid
from datetime import date, timedelta
from decimal import ROUND_DOWN, Decimal
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    CategoryForm,
    ContributionForm,
    HouseholdForm,
    HouseholdListForm,
    HouseholdListItemForm,
    InvestmentGoalForm,
    MemberAddForm,
    ProfileForm,
    RecurringTransactionForm,
    RegistrationForm,
    TransactionForm,
)
from .models import (
    Category,
    Household,
    HouseholdList,
    HouseholdMembership,
    InvestmentContribution,
    InvestmentGoal,
    PaymentMethod,
    RecurringTransaction,
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


MONTHS_PT = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

CATEGORY_COLORS = [
    "#EC4899", "#F43F5E", "#EF4444", "#F97316", "#F59E0B", "#84CC16",
    "#10B981", "#14B8A6", "#06B6D4", "#3B82F6", "#6366F1", "#8B5CF6",
]


def _resolve_month(request):
    """Reference month (1st day) from ?month=YYYY-MM, defaulting to the current month."""
    today = timezone.localdate()
    ref = today.replace(day=1)
    raw = request.GET.get("month")
    if raw:
        try:
            year, month = raw.split("-")
            ref = date(int(year), int(month), 1)
        except (ValueError, TypeError):
            pass
    prev_month = (ref - timedelta(days=1)).replace(day=1)
    next_month = (ref.replace(day=28) + timedelta(days=7)).replace(day=1)
    return {
        "ref_month": ref,
        "prev_month": prev_month.strftime("%Y-%m"),
        "next_month": next_month.strftime("%Y-%m"),
        "month_label": f"{MONTHS_PT[ref.month]} {ref.year}",
        "is_current_month": ref == today.replace(day=1),
    }


def _materialize_recurring(user, household, year, month):
    """Create the transaction for each active fixed bill in the given month, once."""
    last_day = calendar.monthrange(year, month)[1]
    bills = RecurringTransaction.objects.in_scope(user, household).filter(
        is_active=True,
        start_date__lte=date(year, month, last_day),
    )
    for bill in bills:
        already = Transaction.objects.filter(
            recurring_source=bill, date__year=year, date__month=month
        ).exists()
        if already:
            continue
        day = min(bill.start_date.day, last_day)
        Transaction.objects.create(
            user=bill.user,
            household=bill.household,
            category=bill.category,
            description=bill.description,
            amount=bill.amount,
            date=date(year, month, day),
            type=bill.type,
            payment_method=bill.payment_method,
            recurring_source=bill,
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
def household_update(request, pk):
    household = get_object_or_404(
        Household.objects.for_user(request.user), pk=pk
    )
    if household.created_by_id != request.user.id:
        messages.error(request, "Apenas o dono do grupo pode editá-lo.")
        return redirect("finances:household_detail", pk=pk)

    if request.method == "POST":
        form = HouseholdForm(request.POST, instance=household)
        if form.is_valid():
            form.save()
            messages.success(request, "Grupo atualizado.")
            return redirect("finances:household_detail", pk=pk)
    else:
        form = HouseholdForm(instance=household)
    return render(
        request,
        "finances/household_form.html",
        {"form": form, "title": "Editar grupo", "submit_label": "Salvar"},
    )


@login_required
def household_delete(request, pk):
    household = get_object_or_404(
        Household.objects.for_user(request.user), pk=pk
    )
    if household.created_by_id != request.user.id:
        messages.error(request, "Apenas o dono do grupo pode excluí-lo.")
        return redirect("finances:household_detail", pk=pk)

    if request.method == "POST":
        # Deleting the active scope leaves a stale id in the session; reset it.
        if request.session.get("active_household_id") == household.pk:
            request.session.pop("active_household_id", None)
        with transaction.atomic():
            # Transactions/recurring bills reference categories via PROTECT, so
            # drop them before the household cascade removes the categories.
            # Cover both the group's own entries and any entry (e.g. personal)
            # that still references a group category, or the cascade trips.
            scope = Q(household=household) | Q(category__household=household)
            Transaction.objects.filter(scope).delete()
            RecurringTransaction.objects.filter(scope).delete()
            household.delete()
        messages.success(request, "Grupo excluído.")
        return redirect("finances:household_list")
    return render(
        request,
        "finances/confirm_delete.html",
        {
            "object": household,
            "title": "Excluir grupo",
            "warning": (
                "Isso também apaga todas as categorias, lançamentos, contas "
                "fixas, objetivos e listas do grupo, para todos os membros."
            ),
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
            # Multiple auth backends (django-axes) are configured, so login()
            # needs the backend to use for this session made explicit.
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
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
    """Show a summary of the selected month plus that month's transactions."""
    household = get_active_household(request)
    month = _resolve_month(request)
    ref = month["ref_month"]
    _materialize_recurring(request.user, household, ref.year, ref.month)
    month_qs = Transaction.objects.in_scope(request.user, household).filter(
        date__year=ref.year,
        date__month=ref.month,
    )

    income = month_qs.filter(type=TransactionType.INCOME).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")
    expense_qs = month_qs.filter(type=TransactionType.EXPENSE)
    expense = expense_qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Credit card spending for the month; it is a subset of expense, not extra.
    credit_card = expense_qs.filter(
        payment_method=PaymentMethod.CREDIT_CARD,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    # Expense breakdowns for the selected month, by category and payment method.
    by_category = [
        {
            "name": row["category__name"],
            "color": row["category__color"],
            "total": row["total"],
            "percent": row["total"] / expense * 100 if expense else 0,
        }
        for row in expense_qs.values("category__name", "category__color")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    ]
    by_payment = [
        {
            "label": PaymentMethod(row["payment_method"]).label,
            "total": row["total"],
            "percent": row["total"] / expense * 100 if expense else 0,
        }
        for row in expense_qs.values("payment_method")
        .annotate(total=Sum("amount"))
        .order_by("-total")
    ]

    # Investment contributions in the active scope count as money out of the cash flow.
    invested = InvestmentContribution.objects.filter(
        goal__in=InvestmentGoal.objects.in_scope(request.user, household),
        date__year=ref.year,
        date__month=ref.month,
    ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

    context = {
        **month,
        "income": income,
        "expense": expense,
        "credit_card": credit_card,
        "by_category": by_category,
        "by_payment": by_payment,
        "invested": invested,
        "balance": income - expense - invested,
        "recent": month_qs.select_related("category")[:10],
    }
    return render(request, "finances/dashboard.html", context)


@login_required
def forecast(request):
    """Project the next months: real transactions plus fixed bills not yet materialized."""
    household = get_active_household(request)
    base = timezone.localdate().replace(day=1)
    bills = list(
        RecurringTransaction.objects.in_scope(request.user, household).filter(
            is_active=True
        )
    )
    months = []
    running = Decimal("0")
    for i in range(6):
        ref = _add_months(base, i)
        last_day = calendar.monthrange(ref.year, ref.month)[1]
        month_end = date(ref.year, ref.month, last_day)
        scope_tx = Transaction.objects.in_scope(request.user, household).filter(
            date__year=ref.year, date__month=ref.month
        )
        income = scope_tx.filter(type=TransactionType.INCOME).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")
        expense = scope_tx.filter(type=TransactionType.EXPENSE).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")
        invested = InvestmentContribution.objects.filter(
            goal__in=InvestmentGoal.objects.in_scope(request.user, household),
            date__year=ref.year,
            date__month=ref.month,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # Committed expense = installments + recurring-generated outflows already
        # scheduled (near-certain), as opposed to free/discretionary spending.
        committed = scope_tx.filter(type=TransactionType.EXPENSE).filter(
            Q(installment_group__isnull=False) | Q(recurring_source__isnull=False)
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # Add fixed bills that have not been materialized into this month yet,
        # so projected months are not double-counted against real transactions.
        materialized = set(
            scope_tx.exclude(recurring_source=None).values_list(
                "recurring_source_id", flat=True
            )
        )
        for bill in bills:
            if bill.start_date > month_end or bill.id in materialized:
                continue
            if bill.type == TransactionType.INCOME:
                income += bill.amount
            else:
                expense += bill.amount
                committed += bill.amount

        balance = income - expense - invested
        running += balance
        months.append({
            "label": f"{MONTHS_PT[ref.month]} {ref.year}",
            "short_label": MONTHS_PT[ref.month][:3],
            "month_param": ref.strftime("%Y-%m"),
            "income": income,
            "expense": expense,
            "committed": committed,
            "free": expense - committed,
            "committed_pct": (committed / expense * 100) if expense else 0,
            "balance": balance,
            "cumulative": running,
            "is_current": ref == base,
        })

    # Insights over the 6-month window.
    tightest = min(months, key=lambda m: m["balance"])
    summary = {
        "end_balance": months[-1]["cumulative"],
        "avg_balance": sum((m["balance"] for m in months), Decimal("0")) / len(months),
        "tightest_label": tightest["label"],
        "tightest_balance": tightest["balance"],
        "total_committed": sum((m["committed"] for m in months), Decimal("0")),
    }
    chart = [{"label": m["short_label"], "value": float(m["cumulative"])} for m in months]

    return render(
        request,
        "finances/forecast.html",
        {"months": months, "summary": summary, "chart": chart},
    )


@login_required
def transaction_list(request):
    """List the selected month's transactions in the active scope, with combinable filters."""
    household = get_active_household(request)
    month = _resolve_month(request)
    ref = month["ref_month"]
    _materialize_recurring(request.user, household, ref.year, ref.month)
    transactions = Transaction.objects.in_scope(request.user, household).filter(
        date__year=ref.year,
        date__month=ref.month,
    ).select_related("category")

    type_filter = request.GET.get("type")
    if type_filter in TransactionType.values:
        transactions = transactions.filter(type=type_filter)

    category_filter = request.GET.get("category", "")
    if category_filter.isdigit():
        transactions = transactions.filter(category_id=int(category_filter))

    payment_filter = request.GET.get("payment_method", "")
    if payment_filter in PaymentMethod.values:
        transactions = transactions.filter(payment_method=payment_filter)

    query = request.GET.get("q", "").strip()
    if query:
        transactions = transactions.filter(description__icontains=query)

    # Sort by value groups income/expense, each ordered high to low; default is by date.
    sort = "amount" if request.GET.get("sort") == "amount" else "date"
    if sort == "amount":
        transactions = transactions.order_by("-type", "-amount")

    # Summary of the filtered set (answers "how much did I spend on this?").
    income = transactions.filter(type=TransactionType.INCOME).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")
    expense = transactions.filter(type=TransactionType.EXPENSE).aggregate(
        total=Sum("amount")
    )["total"] or Decimal("0")

    # Active filters carried by the month navigation links (month is set separately).
    active = {
        key: value
        for key, value in (
            ("type", type_filter if type_filter in TransactionType.values else ""),
            ("category", category_filter if category_filter.isdigit() else ""),
            ("payment_method", payment_filter if payment_filter in PaymentMethod.values else ""),
            ("q", query),
            ("sort", sort if sort == "amount" else ""),
        )
        if value
    }
    filter_qs = ("&" + urlencode(active)) if active else ""

    return render(
        request,
        "finances/transaction_list.html",
        {
            **month,
            "transactions": transactions,
            "type_filter": type_filter,
            "category_filter": category_filter,
            "payment_filter": payment_filter,
            "query": query,
            "sort": sort,
            "categories": Category.objects.in_scope(request.user, household).filter(
                is_active=True
            ).order_by("nature", "name"),
            "payment_methods": PaymentMethod.choices,
            "summary_income": income,
            "summary_expense": expense,
            "summary_balance": income - expense,
            "has_filters": bool(active),
            "filter_qs": filter_qs,
        },
    )


def _add_months(d, n):
    """Return the date n months after d, clamping the day to the month's length."""
    month_index = d.month - 1 + n
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _save_installments(form, installments):
    """Create one transaction per month, splitting the total amount evenly."""
    base = form.instance
    total = base.amount
    group = uuid.uuid4()
    per = (total / installments).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    with transaction.atomic():
        for i in range(installments):
            # Last installment absorbs the rounding remainder.
            amount = per if i < installments - 1 else total - per * (installments - 1)
            Transaction.objects.create(
                user=base.user,
                household=base.household,
                category=base.category,
                description=base.description,
                amount=amount,
                date=_add_months(base.date, i),
                type=base.type,
                payment_method=base.payment_method,
                notes=base.notes,
                installment_group=group,
                installment_number=i + 1,
                installment_total=installments,
            )


def _is_ajax(request):
    """The launch modal posts with this header; we answer with JSON instead of a page."""
    return request.headers.get("x-requested-with") == "XMLHttpRequest"


def _form_errors(form):
    """Flatten form.errors into {field: [messages]} for the modal to render."""
    return {field: [str(error) for error in errors] for field, errors in form.errors.items()}


@login_required
def transaction_create(request):
    household = get_active_household(request)
    if request.method == "POST":
        form = TransactionForm(
            request.POST, user=request.user, household=household
        )
        if form.is_valid():
            installments = form.cleaned_data.get("installments") or 1
            if installments > 1:
                _save_installments(form, installments)
                messages.success(
                    request, f"Lançamento parcelado em {installments}x criado."
                )
            else:
                form.save()
                messages.success(request, "Lançamento criado.")
            if _is_ajax(request):
                return JsonResponse({"ok": True})
            return redirect("finances:transaction_list")
        if _is_ajax(request):
            return JsonResponse({"ok": False, "errors": _form_errors(form)}, status=400)
    else:
        form = TransactionForm(user=request.user, household=household)
    return render(
        request,
        "finances/transaction_form.html",
        {"form": form, "title": "Novo lançamento"},
    )


@login_required
def transaction_update(request, pk):
    household = get_active_household(request)
    entry = get_object_or_404(
        Transaction.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        form = TransactionForm(
            request.POST,
            instance=entry,
            user=request.user,
            household=household,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Lançamento atualizado.")
            if _is_ajax(request):
                return JsonResponse({"ok": True})
            return redirect("finances:transaction_list")
        if _is_ajax(request):
            return JsonResponse({"ok": False, "errors": _form_errors(form)}, status=400)
    else:
        form = TransactionForm(
            instance=entry, user=request.user, household=household
        )
    return render(
        request,
        "finances/transaction_form.html",
        {"form": form, "title": "Editar lançamento"},
    )


@login_required
def transaction_delete(request, pk):
    household = get_active_household(request)
    entry = get_object_or_404(
        Transaction.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        entry.delete()
        messages.success(request, "Lançamento excluído.")
        return redirect("finances:transaction_list")
    return render(
        request,
        "finances/confirm_delete.html",
        {"object": entry, "title": "Excluir lançamento"},
    )


@login_required
def category_list(request):
    household = get_active_household(request)
    # Order by nature so the template can group categories under Fixa/Variável.
    categories = Category.objects.in_scope(request.user, household).order_by(
        "nature", "name"
    )
    return render(
        request, "finances/category_list.html", {"categories": categories}
    )


@login_required
def category_create(request):
    household = get_active_household(request)
    if request.method == "POST":
        form = CategoryForm(
            request.POST, request.FILES, user=request.user, household=household
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria criada.")
            return redirect("finances:category_list")
    else:
        form = CategoryForm(user=request.user, household=household)
    return render(
        request,
        "finances/category_form.html",
        {"form": form, "title": "Nova categoria", "color_choices": CATEGORY_COLORS},
    )


@login_required
def category_update(request, pk):
    household = get_active_household(request)
    category = get_object_or_404(
        Category.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        form = CategoryForm(
            request.POST,
            request.FILES,
            instance=category,
            user=request.user,
            household=household,
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Categoria atualizada.")
            return redirect("finances:category_list")
    else:
        form = CategoryForm(
            instance=category, user=request.user, household=household
        )
    return render(
        request,
        "finances/category_form.html",
        {"form": form, "title": "Editar categoria", "color_choices": CATEGORY_COLORS},
    )


@login_required
def category_delete(request, pk):
    household = get_active_household(request)
    category = get_object_or_404(
        Category.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        if category.transactions.exists() or category.recurring_transactions.exists():
            messages.error(
                request,
                "Esta categoria ainda tem lançamentos e não pode ser excluída.",
            )
            return redirect("finances:category_list")
        category.delete()
        messages.success(request, "Categoria excluída.")
        return redirect("finances:category_list")
    return render(
        request,
        "finances/confirm_delete.html",
        {"object": category, "title": "Excluir categoria"},
    )


@login_required
def recurring_list(request):
    household = get_active_household(request)
    bills = RecurringTransaction.objects.in_scope(
        request.user, household
    ).select_related("category")
    return render(
        request, "finances/recurring_list.html", {"bills": bills}
    )


@login_required
def recurring_create(request):
    household = get_active_household(request)
    if request.method == "POST":
        form = RecurringTransactionForm(
            request.POST, user=request.user, household=household
        )
        if form.is_valid():
            form.save()
            today = timezone.localdate()
            _materialize_recurring(request.user, household, today.year, today.month)
            messages.success(request, "Conta fixa criada.")
            if _is_ajax(request):
                return JsonResponse({"ok": True})
            return redirect("finances:recurring_list")
        if _is_ajax(request):
            return JsonResponse({"ok": False, "errors": _form_errors(form)}, status=400)
    else:
        form = RecurringTransactionForm(
            user=request.user,
            household=household,
            initial={"start_date": timezone.localdate()},
        )
    return render(
        request,
        "finances/recurring_form.html",
        {"form": form, "title": "Nova conta fixa"},
    )


@login_required
def recurring_update(request, pk):
    household = get_active_household(request)
    bill = get_object_or_404(
        RecurringTransaction.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        form = RecurringTransactionForm(
            request.POST, instance=bill, user=request.user, household=household
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Conta fixa atualizada.")
            return redirect("finances:recurring_list")
    else:
        form = RecurringTransactionForm(
            instance=bill, user=request.user, household=household
        )
    return render(
        request,
        "finances/recurring_form.html",
        {"form": form, "title": "Editar conta fixa"},
    )


@login_required
def recurring_delete(request, pk):
    household = get_active_household(request)
    bill = get_object_or_404(
        RecurringTransaction.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        bill.delete()
        messages.success(request, "Conta fixa excluída.")
        return redirect("finances:recurring_list")
    return render(
        request,
        "finances/confirm_delete.html",
        {"object": bill, "title": "Excluir conta fixa"},
    )


@login_required
def investment_list(request):
    household = get_active_household(request)
    goals = InvestmentGoal.objects.in_scope(request.user, household).with_invested()
    total_invested = sum((g.invested_total for g in goals), Decimal("0"))
    return render(
        request,
        "finances/investment_list.html",
        {"goals": goals, "total_invested": total_invested},
    )


@login_required
def investment_create(request):
    household = get_active_household(request)
    if request.method == "POST":
        form = InvestmentGoalForm(
            request.POST, user=request.user, household=household
        )
        if form.is_valid():
            goal = form.save()
            messages.success(request, "Objetivo criado.")
            return redirect("finances:investment_detail", pk=goal.pk)
    else:
        form = InvestmentGoalForm(user=request.user, household=household)
    return render(
        request,
        "finances/investment_form.html",
        {"form": form, "title": "Novo objetivo"},
    )


@login_required
def investment_update(request, pk):
    household = get_active_household(request)
    goal = get_object_or_404(
        InvestmentGoal.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        form = InvestmentGoalForm(
            request.POST, instance=goal, user=request.user, household=household
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Objetivo atualizado.")
            return redirect("finances:investment_detail", pk=goal.pk)
    else:
        form = InvestmentGoalForm(
            instance=goal, user=request.user, household=household
        )
    return render(
        request,
        "finances/investment_form.html",
        {"form": form, "title": "Editar objetivo"},
    )


@login_required
def investment_delete(request, pk):
    household = get_active_household(request)
    goal = get_object_or_404(
        InvestmentGoal.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        goal.delete()
        messages.success(request, "Objetivo excluído.")
        return redirect("finances:investment_list")
    return render(
        request,
        "finances/confirm_delete.html",
        {"object": goal, "title": "Excluir objetivo"},
    )


@login_required
def investment_detail(request, pk):
    household = get_active_household(request)
    goal = get_object_or_404(
        InvestmentGoal.objects.in_scope(request.user, household), pk=pk
    )
    return render(
        request,
        "finances/investment_detail.html",
        {
            "goal": goal,
            "contributions": goal.contributions.select_related("user"),
            "form": ContributionForm(),
        },
    )


@login_required
def contribution_create(request, pk):
    household = get_active_household(request)
    goal = get_object_or_404(
        InvestmentGoal.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        form = ContributionForm(request.POST)
        if form.is_valid():
            contribution = form.save(commit=False)
            contribution.goal = goal
            contribution.user = request.user
            contribution.save()
            messages.success(request, "Aporte registrado.")
            return redirect("finances:investment_detail", pk=goal.pk)
        return render(
            request,
            "finances/investment_detail.html",
            {
                "goal": goal,
                "contributions": goal.contributions.select_related("user"),
                "form": form,
            },
        )
    return redirect("finances:investment_detail", pk=goal.pk)


@login_required
def contribution_delete(request, pk, contrib_pk):
    household = get_active_household(request)
    goal = get_object_or_404(
        InvestmentGoal.objects.in_scope(request.user, household), pk=pk
    )
    if request.method == "POST":
        InvestmentContribution.objects.filter(goal=goal, pk=contrib_pk).delete()
        messages.success(request, "Aporte removido.")
    return redirect("finances:investment_detail", pk=goal.pk)


def _user_lists(user):
    """Household lists from every group the user belongs to."""
    return HouseholdList.objects.filter(
        household__in=Household.objects.for_user(user)
    )


@login_required
def list_index(request):
    household = get_active_household(request)
    if household is None:
        messages.error(request, "Escolha um grupo para ver as listas da casa.")
        return redirect("finances:scope_switch")
    return render(
        request,
        "finances/list_index.html",
        {"household": household, "lists": household.lists.all()},
    )


@login_required
def list_create(request):
    household = get_active_household(request)
    if household is None:
        messages.error(request, "Escolha um grupo para criar uma lista.")
        return redirect("finances:scope_switch")
    if request.method == "POST":
        form = HouseholdListForm(request.POST)
        if form.is_valid():
            house_list = form.save(commit=False)
            house_list.household = household
            house_list.save()
            messages.success(request, "Lista criada.")
            return redirect("finances:list_detail", pk=house_list.pk)
    else:
        form = HouseholdListForm()
    return render(
        request,
        "finances/list_form.html",
        {"form": form, "title": "Nova lista"},
    )


@login_required
def list_detail(request, pk):
    house_list = get_object_or_404(_user_lists(request.user), pk=pk)
    return render(
        request,
        "finances/list_detail.html",
        {
            "list": house_list,
            "items": house_list.items.all(),
            "form": HouseholdListItemForm(),
        },
    )


@login_required
def list_delete(request, pk):
    house_list = get_object_or_404(_user_lists(request.user), pk=pk)
    if request.method == "POST":
        house_list.delete()
        messages.success(request, "Lista excluída.")
        return redirect("finances:list_index")
    return render(
        request,
        "finances/confirm_delete.html",
        {"object": house_list, "title": "Excluir lista"},
    )


@login_required
def list_item_add(request, pk):
    house_list = get_object_or_404(_user_lists(request.user), pk=pk)
    if request.method == "POST":
        form = HouseholdListItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.list = house_list
            item.save()
    return redirect("finances:list_detail", pk=house_list.pk)


@login_required
def list_item_toggle(request, pk, item_pk):
    house_list = get_object_or_404(_user_lists(request.user), pk=pk)
    if request.method == "POST":
        item = get_object_or_404(house_list.items, pk=item_pk)
        item.is_done = not item.is_done
        item.save(update_fields=["is_done"])
    return redirect("finances:list_detail", pk=house_list.pk)


@login_required
def list_item_delete(request, pk, item_pk):
    house_list = get_object_or_404(_user_lists(request.user), pk=pk)
    if request.method == "POST":
        house_list.items.filter(pk=item_pk).delete()
    return redirect("finances:list_detail", pk=house_list.pk)
