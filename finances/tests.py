from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from .forms import RegistrationForm
from .models import (
    Category,
    Household,
    HouseholdList,
    HouseholdMembership,
    InvestmentContribution,
    InvestmentGoal,
    Profile,
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
