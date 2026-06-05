from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone


def _next_month(ref):
    return (ref.replace(day=28) + timedelta(days=7)).replace(day=1)

from .forms import CategoryForm, RegistrationForm
from .models import (
    Category,
    Household,
    HouseholdList,
    HouseholdMembership,
    InvestmentContribution,
    InvestmentGoal,
    Profile,
    RecurringTransaction,
    Transaction,
)

pytestmark = pytest.mark.django_db


def _make_user(django_user_model, email):
    user = django_user_model.objects.create_user(
        username=email, email=email, password="pass-12345"
    )
    # A complete profile keeps ProfileCompletionMiddleware from redirecting.
    Profile.objects.create(user=user, birth_date=date(1990, 1, 1), phone="11999999999")
    return user


@pytest.fixture
def user(django_user_model):
    return _make_user(django_user_model, "ana@test.com")


@pytest.fixture
def other(django_user_model):
    return _make_user(django_user_model, "bob@test.com")


@pytest.fixture
def household(user):
    h = Household.objects.create(name="Casa", created_by=user)
    HouseholdMembership.objects.create(household=h, user=user)
    return h


def make_transaction(user, category, household=None, type="expense"):
    return Transaction(
        user=user,
        household=household,
        category=category,
        description="Test",
        amount=Decimal("10.00"),
        date=date.today(),
        type=type,
    )


# --- Registration by e-mail -------------------------------------------------


def test_registration_stores_email_as_username():
    form = RegistrationForm(
        data={
            "email": "New@Test.com",
            "password1": "umaSenhaForte123",
            "password2": "umaSenhaForte123",
        }
    )
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.username == "new@test.com"
    assert user.email == "new@test.com"


def test_registration_rejects_duplicate_email(user):
    form = RegistrationForm(
        data={
            "email": "ANA@test.com",
            "password1": "umaSenhaForte123",
            "password2": "umaSenhaForte123",
        }
    )
    assert not form.is_valid()
    assert "email" in form.errors


# --- Households and membership ----------------------------------------------


def test_household_create_adds_creator_as_member(client, user):
    client.force_login(user)
    resp = client.post(reverse("finances:household_create"), {"name": "Casa"})
    assert resp.status_code == 302
    household = Household.objects.get(name="Casa")
    assert household.created_by == user
    assert HouseholdMembership.objects.filter(
        household=household, user=user
    ).exists()


def test_member_add_by_email(client, user, other, household):
    client.force_login(user)
    resp = client.post(
        reverse("finances:member_add", args=[household.pk]),
        {"email": "bob@test.com"},
    )
    assert resp.status_code == 302
    assert HouseholdMembership.objects.filter(
        household=household, user=other
    ).exists()


def test_member_add_nonexistent_email_rejected(client, user, household):
    client.force_login(user)
    client.post(
        reverse("finances:member_add", args=[household.pk]),
        {"email": "ghost@test.com"},
    )
    assert household.memberships.count() == 1


def test_member_add_duplicate_rejected(client, user, other, household):
    HouseholdMembership.objects.create(household=household, user=other)
    client.force_login(user)
    client.post(
        reverse("finances:member_add", args=[household.pk]),
        {"email": "bob@test.com"},
    )
    assert (
        HouseholdMembership.objects.filter(
            household=household, user=other
        ).count()
        == 1
    )


def test_non_owner_cannot_add_member(client, other, household):
    HouseholdMembership.objects.create(household=household, user=other)
    client.force_login(other)
    client.post(
        reverse("finances:member_add", args=[household.pk]),
        {"email": "bob@test.com"},
    )
    # still only the original two memberships, no third one created
    assert household.memberships.count() == 2


def test_owner_can_update_household(client, user, household):
    client.force_login(user)
    resp = client.post(
        reverse("finances:household_update", args=[household.pk]),
        {"name": "Casa Nova"},
    )
    assert resp.status_code == 302
    household.refresh_from_db()
    assert household.name == "Casa Nova"


def test_non_owner_cannot_update_household(client, other, household):
    HouseholdMembership.objects.create(household=household, user=other)
    client.force_login(other)
    client.post(
        reverse("finances:household_update", args=[household.pk]),
        {"name": "Hijacked"},
    )
    household.refresh_from_db()
    assert household.name == "Casa"


def test_owner_can_delete_household(client, user, household):
    client.force_login(user)
    resp = client.post(reverse("finances:household_delete", args=[household.pk]))
    assert resp.status_code == 302
    assert not Household.objects.filter(pk=household.pk).exists()


def test_non_owner_cannot_delete_household(client, other, household):
    HouseholdMembership.objects.create(household=household, user=other)
    client.force_login(other)
    client.post(reverse("finances:household_delete", args=[household.pk]))
    assert Household.objects.filter(pk=household.pk).exists()


def test_owner_can_delete_household_with_data(client, user, household):
    category = Category.objects.create(
        user=user, household=household, name="Mercado", type="expense"
    )
    make_transaction(user, category, household=household).save()
    client.force_login(user)
    resp = client.post(reverse("finances:household_delete", args=[household.pk]))
    assert resp.status_code == 302
    assert not Household.objects.filter(pk=household.pk).exists()
    assert not Category.objects.filter(pk=category.pk).exists()
    assert not Transaction.objects.filter(household=household).exists()


def test_household_delete_clears_active_scope(client, user, household):
    client.force_login(user)
    session = client.session
    session["active_household_id"] = household.pk
    session.save()
    client.post(reverse("finances:household_delete", args=[household.pk]))
    assert client.session.get("active_household_id") is None


# --- Scope isolation --------------------------------------------------------


def test_personal_and_group_isolation(user, other, household):
    HouseholdMembership.objects.create(household=household, user=other)
    cp = Category.objects.create(user=user, name="Pessoal", type="expense")
    cg = Category.objects.create(
        user=user, household=household, name="Mercado", type="expense"
    )
    make_transaction(user, cp).save()
    make_transaction(user, cg, household=household).save()

    assert Transaction.objects.in_scope(user, None).count() == 1
    assert Transaction.objects.in_scope(user, household).count() == 1
    # other user sees the group transaction but none of user's personal ones
    assert Transaction.objects.in_scope(other, None).count() == 0
    assert Transaction.objects.in_scope(other, household).count() == 1


def test_non_member_not_in_for_user(other, household):
    assert household not in Household.objects.for_user(other)


# --- Transaction.clean by scope ---------------------------------------------


def test_group_transaction_requires_group_category(user, household):
    personal_cat = Category.objects.create(
        user=user, name="Pessoal", type="expense"
    )
    tx = make_transaction(user, personal_cat, household=household)
    with pytest.raises(ValidationError):
        tx.full_clean()


def test_personal_transaction_rejects_group_category(user, household):
    group_cat = Category.objects.create(
        user=user, household=household, name="Mercado", type="expense"
    )
    tx = make_transaction(user, group_cat, household=None)
    with pytest.raises(ValidationError):
        tx.full_clean()


def test_transaction_type_must_match_category(user):
    income_cat = Category.objects.create(
        user=user, name="Salário", type="income"
    )
    tx = make_transaction(user, income_cat, type="expense")
    with pytest.raises(ValidationError):
        tx.full_clean()


# --- Scope switch -----------------------------------------------------------


def test_scope_switch_to_group(client, user, household):
    client.force_login(user)
    client.post(reverse("finances:scope_switch"), {"scope": str(household.pk)})
    assert client.session["active_household_id"] == household.pk


def test_scope_switch_rejects_non_member_group(client, other, household):
    client.force_login(other)
    client.post(reverse("finances:scope_switch"), {"scope": str(household.pk)})
    assert "active_household_id" not in client.session


# --- Category uniqueness per scope ------------------------------------------


def test_category_unique_per_personal_scope(user):
    Category.objects.create(user=user, name="Mercado", type="expense")
    with pytest.raises(Exception):
        Category.objects.create(user=user, name="Mercado", type="expense")


def test_same_name_allowed_across_scopes(user, household):
    Category.objects.create(user=user, name="Mercado", type="expense")
    # same name is fine in the group scope
    Category.objects.create(
        user=user, household=household, name="Mercado", type="expense"
    )
    assert Category.objects.filter(name="Mercado").count() == 2


# --- Investments ------------------------------------------------------------


def test_goal_progress(user):
    goal = InvestmentGoal.objects.create(
        user=user, name="Viagem", target_amount=Decimal("1000")
    )
    InvestmentContribution.objects.create(
        goal=goal, user=user, amount=Decimal("250"), date=date.today()
    )
    InvestmentContribution.objects.create(
        goal=goal, user=user, amount=Decimal("150"), date=date.today()
    )
    assert goal.invested == Decimal("400")
    assert goal.progress == 40


def test_goal_with_invested_annotation_avoids_extra_query(user, django_assert_num_queries):
    goal = InvestmentGoal.objects.create(
        user=user, name="Viagem", target_amount=Decimal("1000")
    )
    InvestmentContribution.objects.create(
        goal=goal, user=user, amount=Decimal("250"), date=date.today()
    )
    goals = list(InvestmentGoal.objects.in_scope(user, None).with_invested())
    # invested/progress read the annotation, so no per-goal aggregate query.
    with django_assert_num_queries(0):
        assert goals[0].invested == Decimal("250")
        assert goals[0].progress == 25


def test_goal_progress_capped_at_100(user):
    goal = InvestmentGoal.objects.create(
        user=user, name="Meta baixa", target_amount=Decimal("100")
    )
    InvestmentContribution.objects.create(
        goal=goal, user=user, amount=Decimal("500"), date=date.today()
    )
    assert goal.progress == 100


def test_goal_scope_isolation(user, other, household):
    HouseholdMembership.objects.create(household=household, user=other)
    InvestmentGoal.objects.create(
        user=user, name="Pessoal", target_amount=Decimal("100")
    )
    InvestmentGoal.objects.create(
        user=user, household=household, name="Grupo", target_amount=Decimal("100")
    )
    assert InvestmentGoal.objects.in_scope(user, None).count() == 1
    assert InvestmentGoal.objects.in_scope(user, household).count() == 1
    # other sees the group goal but not user's personal one
    assert InvestmentGoal.objects.in_scope(other, None).count() == 0
    assert InvestmentGoal.objects.in_scope(other, household).count() == 1


def test_contribution_counts_as_expense_in_dashboard(client, user):
    goal = InvestmentGoal.objects.create(
        user=user, name="Viagem", target_amount=Decimal("1000")
    )
    InvestmentContribution.objects.create(
        goal=goal, user=user, amount=Decimal("200"), date=date.today()
    )
    client.force_login(user)
    resp = client.get(reverse("finances:dashboard"))
    assert resp.context["invested"] == Decimal("200")
    # balance = income - expense - invested
    assert resp.context["balance"] == Decimal("-200")


def test_contribution_create_view(client, user):
    goal = InvestmentGoal.objects.create(
        user=user, name="Viagem", target_amount=Decimal("1000")
    )
    client.force_login(user)
    client.post(
        reverse("finances:contribution_create", args=[goal.pk]),
        {"amount": "300", "date": date.today().isoformat()},
    )
    assert goal.contributions.count() == 1


def test_non_member_cannot_open_group_goal(client, other, household):
    goal = InvestmentGoal.objects.create(
        user=household.created_by,
        household=household,
        name="Grupo",
        target_amount=Decimal("100"),
    )
    client.force_login(other)  # not a member
    resp = client.get(reverse("finances:investment_detail", args=[goal.pk]))
    assert resp.status_code == 404


# --- Household lists (group only) -------------------------------------------


def test_list_create_requires_group_scope(client, user):
    client.force_login(user)  # personal scope (no active household)
    resp = client.post(reverse("finances:list_create"), {"name": "Compras"})
    assert resp.status_code == 302
    assert resp.url == reverse("finances:scope_switch")
    assert HouseholdList.objects.count() == 0


def test_list_and_item_flow(client, user, household):
    client.force_login(user)
    client.post(reverse("finances:scope_switch"), {"scope": str(household.pk)})
    client.post(reverse("finances:list_create"), {"name": "Compras"})
    house_list = HouseholdList.objects.get(name="Compras")
    assert house_list.household == household

    client.post(
        reverse("finances:list_item_add", args=[house_list.pk]), {"text": "Arroz"}
    )
    item = house_list.items.get()
    assert item.text == "Arroz" and item.is_done is False

    client.post(
        reverse("finances:list_item_toggle", args=[house_list.pk, item.pk])
    )
    item.refresh_from_db()
    assert item.is_done is True


def test_non_member_cannot_open_list(client, other, household):
    house_list = HouseholdList.objects.create(household=household, name="Compras")
    client.force_login(other)  # not a member
    resp = client.get(reverse("finances:list_detail", args=[house_list.pk]))
    assert resp.status_code == 404


# --- Category duplicate handling via form/view (RF06) -----------------------

CAT_DATA = {"name": "Mercado", "type": "expense", "color": "#3498db", "is_active": "on"}


def test_category_form_rejects_duplicate_personal(user):
    Category.objects.create(user=user, name="Mercado", type="expense")
    form = CategoryForm(CAT_DATA, user=user, household=None)
    assert not form.is_valid()
    assert "__all__" in form.errors


def test_category_form_rejects_duplicate_group(user, household):
    Category.objects.create(
        user=user, household=household, name="Mercado", type="expense"
    )
    form = CategoryForm(CAT_DATA, user=user, household=household)
    assert not form.is_valid()


def test_category_form_allows_same_name_other_scope(user, household):
    Category.objects.create(user=user, name="Mercado", type="expense")
    form = CategoryForm(CAT_DATA, user=user, household=household)
    assert form.is_valid(), form.errors


def test_category_create_view_handles_duplicate(client, user):
    client.force_login(user)
    client.post(reverse("finances:category_create"), CAT_DATA)
    resp = client.post(reverse("finances:category_create"), CAT_DATA)
    # second submit is re-rendered with an error, not a 500
    assert resp.status_code == 200
    assert Category.objects.filter(user=user, name="Mercado").count() == 1


def test_delete_confirm_pages_render(client, user, household):
    # The confirm_delete template must render on GET for every model that reuses it.
    cat = Category.objects.create(user=user, name="Mercado", type="expense")
    client.force_login(user)
    assert client.get(reverse("finances:category_delete", args=[cat.pk])).status_code == 200
    assert client.get(reverse("finances:household_delete", args=[household.pk])).status_code == 200


def test_category_create_accepts_image_icon(client, user, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    import io

    from django.core.files.uploadedfile import SimpleUploadedFile
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "pink").save(buf, "PNG")
    buf.seek(0)
    icon = SimpleUploadedFile("icon.png", buf.read(), content_type="image/png")

    client.force_login(user)
    resp = client.post(
        reverse("finances:category_create"), {**CAT_DATA, "icon": icon}
    )
    assert resp.status_code == 302
    cat = Category.objects.get(user=user, name="Mercado")
    assert cat.icon.name.startswith("category_icons/")


def test_category_update_keeps_creator(client, user, other, household):
    HouseholdMembership.objects.create(household=household, user=other)
    cat = Category.objects.create(
        user=user, household=household, name="Mercado", type="expense"
    )
    client.force_login(other)
    client.post(reverse("finances:scope_switch"), {"scope": str(household.pk)})
    client.post(
        reverse("finances:category_update", args=[cat.pk]),
        {**CAT_DATA, "name": "Mercado 2"},
    )
    cat.refresh_from_db()
    assert cat.name == "Mercado 2"
    assert cat.user == user  # editing does not steal authorship


# --- Login by e-mail is case-insensitive ------------------------------------


def test_login_case_insensitive(client, user):
    resp = client.post(
        reverse("login"), {"username": "ANA@Test.com", "password": "pass-12345"}
    )
    assert resp.status_code == 302


def test_login_wrong_password_fails(client, user):
    resp = client.post(
        reverse("login"), {"username": "ana@test.com", "password": "wrong"}
    )
    assert resp.status_code == 200  # re-rendered, not authenticated


# --- Brute-force lockout (django-axes) --------------------------------------


def test_login_lockout_after_failures(client, user):
    for _ in range(5):
        client.post(
            reverse("login"), {"username": "ana@test.com", "password": "wrong"}
        )
    # once locked out, even the correct password is blocked
    resp = client.post(
        reverse("login"), {"username": "ana@test.com", "password": "pass-12345"}
    )
    assert resp.status_code == 429


# --- Month navigation -------------------------------------------------------


def test_dashboard_and_list_filter_by_month(client, user):
    cat = Category.objects.create(user=user, name="Mercado", type="expense")
    this_month = timezone.localdate().replace(day=10)
    nxt = _next_month(this_month).replace(day=15)
    Transaction.objects.create(
        user=user, category=cat, description="Deste mês",
        amount=Decimal("50"), date=this_month, type="expense",
    )
    Transaction.objects.create(
        user=user, category=cat, description="Do mês que vem",
        amount=Decimal("80"), date=nxt, type="expense",
    )
    client.force_login(user)

    # default = current month
    resp = client.get(reverse("finances:dashboard"))
    assert resp.context["expense"] == Decimal("50")

    # ?month= shows the future month
    resp2 = client.get(
        reverse("finances:dashboard"), {"month": nxt.strftime("%Y-%m")}
    )
    assert resp2.context["expense"] == Decimal("80")

    # the list view filters by month too
    resp3 = client.get(
        reverse("finances:transaction_list"), {"month": nxt.strftime("%Y-%m")}
    )
    descriptions = [t.description for t in resp3.context["transactions"]]
    assert descriptions == ["Do mês que vem"]


# --- Installments -----------------------------------------------------------


def test_installments_split_across_months(client, user):
    cat = Category.objects.create(user=user, name="Eletro", type="expense")
    client.force_login(user)
    client.post(reverse("finances:transaction_create"), {
        "description": "Geladeira", "amount": "1000.00", "date": "2026-06-15",
        "type": "expense", "category": str(cat.pk),
        "payment_method": "credit_card", "installments": "3",
    })
    txs = list(Transaction.objects.filter(user=user).order_by("date"))
    assert len(txs) == 3
    # last installment absorbs the rounding remainder
    assert [t.amount for t in txs] == [
        Decimal("333.33"), Decimal("333.33"), Decimal("333.34")
    ]
    assert [t.date.month for t in txs] == [6, 7, 8]
    assert [t.installment_number for t in txs] == [1, 2, 3]
    assert all(t.installment_total == 3 for t in txs)
    assert len({t.installment_group for t in txs}) == 1
    assert txs[0].installment_label == "1/3"


def test_installments_single_is_plain(client, user):
    cat = Category.objects.create(user=user, name="Mercado", type="expense")
    client.force_login(user)
    client.post(reverse("finances:transaction_create"), {
        "description": "Pão", "amount": "10.00", "date": "2026-06-15",
        "type": "expense", "category": str(cat.pk),
        "payment_method": "cash", "installments": "1",
    })
    t = Transaction.objects.get(user=user)
    assert t.installment_group is None
    assert t.installment_label == ""


def test_installments_insufficient_amount_rejected(client, user):
    cat = Category.objects.create(user=user, name="Mercado", type="expense")
    client.force_login(user)
    resp = client.post(reverse("finances:transaction_create"), {
        "description": "Bala", "amount": "0.02", "date": "2026-06-15",
        "type": "expense", "category": str(cat.pk),
        "payment_method": "cash", "installments": "5",
    })
    assert resp.status_code == 200
    assert Transaction.objects.filter(user=user).count() == 0


# --- Recurring (fixed bills) ------------------------------------------------


def _make_bill(user, cat, **kw):
    defaults = dict(
        user=user, category=cat, description="Aluguel",
        amount=Decimal("1500"), type="expense", start_date=date(2026, 6, 5),
    )
    defaults.update(kw)
    return RecurringTransaction.objects.create(**defaults)


def test_recurring_materializes_on_month_open(client, user):
    cat = Category.objects.create(user=user, name="Moradia", type="expense")
    bill = _make_bill(user, cat)
    client.force_login(user)
    client.get(reverse("finances:dashboard"), {"month": "2026-06"})
    gen = Transaction.objects.filter(recurring_source=bill, date__month=6)
    assert gen.count() == 1
    assert gen.first().date == date(2026, 6, 5)
    assert gen.first().amount == Decimal("1500")
    # opening the same month again does not duplicate
    client.get(reverse("finances:dashboard"), {"month": "2026-06"})
    assert Transaction.objects.filter(recurring_source=bill, date__month=6).count() == 1


def test_recurring_materializes_future_month(client, user):
    cat = Category.objects.create(user=user, name="Moradia", type="expense")
    bill = _make_bill(user, cat)
    client.force_login(user)
    client.get(reverse("finances:transaction_list"), {"month": "2026-09"})
    assert Transaction.objects.filter(
        recurring_source=bill, date=date(2026, 9, 5)
    ).exists()


def test_recurring_not_before_start(client, user):
    cat = Category.objects.create(user=user, name="Moradia", type="expense")
    bill = _make_bill(user, cat)
    client.force_login(user)
    client.get(reverse("finances:dashboard"), {"month": "2026-05"})
    assert not Transaction.objects.filter(recurring_source=bill).exists()


def test_recurring_inactive_not_generated(client, user):
    cat = Category.objects.create(user=user, name="Moradia", type="expense")
    bill = _make_bill(user, cat, is_active=False)
    client.force_login(user)
    client.get(reverse("finances:dashboard"), {"month": "2026-06"})
    assert not Transaction.objects.filter(recurring_source=bill).exists()


def test_recurring_create_view(client, user):
    cat = Category.objects.create(user=user, name="Moradia", type="expense")
    client.force_login(user)
    client.post(reverse("finances:recurring_create"), {
        "description": "Internet", "amount": "100.00", "type": "expense",
        "category": str(cat.pk), "payment_method": "pix",
        "start_date": "2026-06-10", "is_active": "on",
    })
    assert RecurringTransaction.objects.filter(
        user=user, description="Internet"
    ).exists()


def test_category_delete_blocked_by_recurring(client, user):
    cat = Category.objects.create(user=user, name="Moradia", type="expense")
    _make_bill(user, cat)
    client.force_login(user)
    client.post(reverse("finances:category_delete", args=[cat.pk]))
    # PROTECT: a category used by a fixed bill cannot be deleted
    assert Category.objects.filter(pk=cat.pk).exists()


def test_recurring_scope_isolation(user, other, household):
    HouseholdMembership.objects.create(household=household, user=other)
    cat_p = Category.objects.create(user=user, name="Pessoal", type="expense")
    cat_g = Category.objects.create(
        user=user, household=household, name="Casa", type="expense"
    )
    _make_bill(user, cat_p)
    _make_bill(user, cat_g, household=household, description="Aluguel casa")
    assert RecurringTransaction.objects.in_scope(user, None).count() == 1
    assert RecurringTransaction.objects.in_scope(user, household).count() == 1
    assert RecurringTransaction.objects.in_scope(other, None).count() == 0
    assert RecurringTransaction.objects.in_scope(other, household).count() == 1


# --- Forecast ---------------------------------------------------------------


def test_forecast_projects_and_does_not_double_count(client, user):
    cat = Category.objects.create(user=user, name="Moradia", type="expense")
    today = timezone.localdate()
    _make_bill(user, cat, amount=Decimal("1000"), start_date=today.replace(day=5))
    client.force_login(user)
    resp = client.get(reverse("finances:forecast"))
    months = resp.context["months"]
    assert len(months) == 6
    assert months[0]["is_current"] is True
    # the fixed bill is projected into the current and later months
    assert months[0]["expense"] == Decimal("1000")
    assert months[3]["expense"] == Decimal("1000")
    # opening the current month materializes the bill; forecast must not double it
    client.get(reverse("finances:dashboard"))
    resp2 = client.get(reverse("finances:forecast"))
    assert resp2.context["months"][0]["expense"] == Decimal("1000")


# --- Dashboard breakdowns ---------------------------------------------------


def test_dashboard_breaks_down_expenses_by_category_and_payment(client, user):
    market = Category.objects.create(user=user, name="Mercado", type="expense")
    transport = Category.objects.create(user=user, name="Transporte", type="expense")
    income_cat = Category.objects.create(user=user, name="Salário", type="income")
    today = timezone.localdate().replace(day=10)
    Transaction.objects.create(
        user=user, category=market, description="Compra",
        amount=Decimal("300"), date=today, type="expense",
        payment_method="credit_card",
    )
    Transaction.objects.create(
        user=user, category=transport, description="Uber",
        amount=Decimal("100"), date=today, type="expense",
        payment_method="pix",
    )
    # income must not leak into the expense breakdowns
    Transaction.objects.create(
        user=user, category=income_cat, description="Pagamento",
        amount=Decimal("5000"), date=today, type="income",
        payment_method="bank_transfer",
    )
    client.force_login(user)
    resp = client.get(reverse("finances:dashboard"))

    by_category = {row["name"]: row["total"] for row in resp.context["by_category"]}
    assert by_category == {"Mercado": Decimal("300"), "Transporte": Decimal("100")}

    by_payment = {row["label"]: row["total"] for row in resp.context["by_payment"]}
    assert by_payment == {"Cartão de crédito": Decimal("300"), "Pix": Decimal("100")}
