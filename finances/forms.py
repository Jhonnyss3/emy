from decimal import Decimal

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import (
    Category,
    Household,
    HouseholdList,
    HouseholdListItem,
    InvestmentContribution,
    InvestmentGoal,
    Profile,
    RecurringTransaction,
    Transaction,
)


class HouseholdForm(forms.ModelForm):
    class Meta:
        model = Household
        fields = ("name",)
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex.: Casa"}),
        }


class EmailAuthenticationForm(AuthenticationForm):
    """Log in by e-mail, matching the lowercase username stored at sign-up."""

    def clean_username(self):
        return self.cleaned_data.get("username", "").strip().lower()


class MemberAddForm(forms.Form):
    email = forms.EmailField()

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        user = User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email)
        ).first()
        if user is None:
            raise ValidationError(
                "Não foi possível adicionar este e-mail ao grupo."
            )
        self.user = user
        return email


class RegistrationForm(UserCreationForm):
    """Sign up using the e-mail as the identifier (stored as the username too)."""

    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(
            Q(email__iexact=email) | Q(username__iexact=email)
        ).exists():
            raise ValidationError("Já existe uma conta com este e-mail.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "type", "color", "icon", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Groceries"}),
            "type": forms.Select(),
            "color": forms.TextInput(attrs={"type": "color"}),
        }

    def __init__(self, *args, user=None, household=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.household = household

    def clean(self):
        cleaned_data = super().clean()
        # On create, attach owner and scope so the uniqueness check can run.
        if self.instance.pk is None:
            if self.user is not None:
                self.instance.user = self.user
            self.instance.household = self.household
        return cleaned_data

    def _get_validation_exclusions(self):
        # user and household are not form fields, so they would be excluded and
        # the scoped unique constraints skipped. Keep them so full_clean runs them.
        exclude = super()._get_validation_exclusions()
        exclude.discard("user")
        exclude.discard("household")
        return exclude


class TransactionForm(forms.ModelForm):
    # Non-model field: how many monthly installments to split this entry into.
    installments = forms.IntegerField(
        required=False, min_value=1, max_value=60, initial=1
    )

    class Meta:
        model = Transaction
        fields = (
            "description",
            "amount",
            "date",
            "type",
            "category",
            "payment_method",
            "notes",
        )
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, user=None, household=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.household = household
        # Only show active categories from the active scope (personal or group).
        if user is not None:
            self.fields["category"].queryset = Category.objects.in_scope(
                user, household
            ).filter(is_active=True)

    def clean_installments(self):
        return self.cleaned_data.get("installments") or 1

    def clean(self):
        cleaned_data = super().clean()
        # Attach owner and scope before model.clean() runs the cross-field checks.
        if self.user is not None:
            self.instance.user = self.user
        self.instance.household = self.household
        # Each installment must still be worth at least the minimum amount.
        installments = cleaned_data.get("installments") or 1
        amount = cleaned_data.get("amount")
        if installments > 1 and amount is not None:
            if amount < Decimal("0.01") * installments:
                self.add_error(
                    "installments",
                    "Valor insuficiente para esse número de parcelas.",
                )
        return cleaned_data


class RecurringTransactionForm(forms.ModelForm):
    class Meta:
        model = RecurringTransaction
        fields = (
            "description",
            "amount",
            "type",
            "category",
            "payment_method",
            "start_date",
            "is_active",
        )
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
        }

    def __init__(self, *args, user=None, household=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.household = household
        if user is not None:
            self.fields["category"].queryset = Category.objects.in_scope(
                user, household
            ).filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        if self.user is not None:
            self.instance.user = self.user
        self.instance.household = self.household
        return cleaned_data


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta:
        model = Profile
        fields = ("first_name", "last_name", "birth_date", "phone")
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
            "phone": forms.TextInput(attrs={"placeholder": "(11) 99999-9999"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if self.user is not None:
            profile.user = self.user
            self.user.first_name = self.cleaned_data["first_name"]
            self.user.last_name = self.cleaned_data["last_name"]
            if commit:
                self.user.save()
        if commit:
            profile.save()
        return profile


class InvestmentGoalForm(forms.ModelForm):
    class Meta:
        model = InvestmentGoal
        fields = ("name", "target_amount", "target_date")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex.: Reserva de emergência"}),
            "target_amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "target_date": forms.DateInput(attrs={"type": "date"}),
        }


class ContributionForm(forms.ModelForm):
    class Meta:
        model = InvestmentContribution
        fields = ("amount", "date", "notes")
        widgets = {
            "amount": forms.NumberInput(attrs={"step": "0.01", "min": "0.01"}),
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class HouseholdListForm(forms.ModelForm):
    class Meta:
        model = HouseholdList
        fields = ("name",)
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ex.: Compras"}),
        }


class HouseholdListItemForm(forms.ModelForm):
    class Meta:
        model = HouseholdListItem
        fields = ("text",)
        widgets = {
            "text": forms.TextInput(attrs={"placeholder": "Adicionar item"}),
        }
