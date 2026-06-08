from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models.functions import Coalesce


class TransactionType(models.TextChoices):
    """Whether money comes in or goes out."""

    INCOME = "income", "Receita"
    EXPENSE = "expense", "Despesa"


class PaymentMethod(models.TextChoices):
    """How a transaction was settled."""

    CASH = "cash", "Dinheiro"
    DEBIT_CARD = "debit_card", "Cartão de débito"
    CREDIT_CARD = "credit_card", "Cartão de crédito"
    PIX = "pix", "Pix"
    BANK_SLIP = "bank_slip", "Boleto"
    BANK_TRANSFER = "bank_transfer", "Transferência"


class CategoryNature(models.TextChoices):
    """Whether a category repeats every month (fixed) or changes (variable)."""

    FIXED = "fixed", "Fixa"
    VARIABLE = "variable", "Variável"


hex_color_validator = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
    message="A cor deve ser um valor hexadecimal, ex.: #1abc9c.",
)

phone_validator = RegexValidator(
    regex=r"^\+?[0-9\s()\-]{8,20}$",
    message="Informe um telefone válido.",
)


class ScopedQuerySet(models.QuerySet):
    """Shared scope filter: personal (household IS NULL) or a specific group."""

    def in_scope(self, user, household):
        if household is None:
            return self.filter(user=user, household__isnull=True)
        return self.filter(household=household)


class NameTrimMixin:
    """Trim the name and reject a blank one. Shared by named models."""

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "O nome não pode ficar em branco."})


class ScopedEntryMixin:
    """Shared clean() for entries that reference a scoped Category."""

    def clean(self):
        super().clean()
        if self.description:
            self.description = self.description.strip()

        if self.category_id:
            # The category must belong to the same scope as the entry.
            if self.household_id:
                if self.category.household_id != self.household_id:
                    raise ValidationError(
                        {"category": "A categoria deve ser do mesmo grupo."}
                    )
            elif self.user_id:
                if (
                    self.category.household_id is not None
                    or self.category.user_id != self.user_id
                ):
                    raise ValidationError(
                        {"category": "A categoria deve ser do mesmo usuário."}
                    )

            # The category type must match the entry type.
            if self.type and self.category.type != self.type:
                raise ValidationError(
                    {
                        "category": (
                            "O tipo da categoria não corresponde ao tipo do "
                            "lançamento."
                        )
                    }
                )


class Profile(models.Model):
    """Extra personal data for a user, filled in right after sign-up."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    birth_date = models.DateField()
    phone = models.CharField(max_length=20, validators=[phone_validator])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class HouseholdManager(models.Manager):
    def for_user(self, user):
        """Households the given user is a member of."""
        return self.filter(memberships__user=user)


class Household(NameTrimMixin, models.Model):
    """A shared space where several users track finances together."""

    name = models.CharField(max_length=80)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_households",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HouseholdManager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class HouseholdMembership(models.Model):
    """Links a user to a household they belong to."""

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="household_memberships",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["household", "user"],
                name="unique_household_member",
            )
        ]

    def __str__(self):
        return f"{self.user.username} in {self.household.name}"


class Category(NameTrimMixin, models.Model):
    """A user-defined bucket that classifies transactions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="categories",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=80)
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    nature = models.CharField(
        max_length=10,
        choices=CategoryNature.choices,
        default=CategoryNature.VARIABLE,
    )
    color = models.CharField(
        max_length=7,
        default="#3498db",
        validators=[hex_color_validator],
    )
    icon = models.ImageField(upload_to="category_icons/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ScopedQuerySet.as_manager()

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name", "type"],
                condition=models.Q(household__isnull=True),
                name="unique_personal_category",
                violation_error_message="Você já tem uma categoria com esse nome e tipo.",
            ),
            models.UniqueConstraint(
                fields=["household", "name", "type"],
                condition=models.Q(household__isnull=False),
                name="unique_household_category",
                violation_error_message="O grupo já tem uma categoria com esse nome e tipo.",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"


class Transaction(ScopedEntryMixin, models.Model):
    """A single income or expense entry, personal or shared in a group."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="transactions",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    date = models.DateField()
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    payment_method = models.CharField(
        max_length=15,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    notes = models.TextField(blank=True)
    # Installment plan: a purchase split across several months shares a group id.
    installment_group = models.UUIDField(
        null=True, blank=True, db_index=True, editable=False
    )
    installment_number = models.PositiveSmallIntegerField(null=True, blank=True)
    installment_total = models.PositiveSmallIntegerField(null=True, blank=True)
    # Set when this entry was generated from a fixed/recurring bill.
    recurring_source = models.ForeignKey(
        "RecurringTransaction",
        on_delete=models.SET_NULL,
        related_name="generated",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = ScopedQuerySet.as_manager()

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.description} - {self.amount}"

    @property
    def signed_amount(self):
        """Amount as a signed value: positive for income, negative for expense."""
        if self.type == TransactionType.EXPENSE:
            return -self.amount
        return self.amount

    @property
    def installment_label(self):
        """Label like '2/12' for installment entries, empty otherwise."""
        if self.installment_total and self.installment_total > 1:
            return f"{self.installment_number}/{self.installment_total}"
        return ""


class RecurringTransaction(ScopedEntryMixin, models.Model):
    """A fixed, open-ended bill (e.g. rent) that recurs every month."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recurring_transactions",
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="recurring_transactions",
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="recurring_transactions",
    )
    description = models.CharField(max_length=200)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    payment_method = models.CharField(
        max_length=15,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH,
    )
    start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = ScopedQuerySet.as_manager()

    class Meta:
        ordering = ["description"]

    def __str__(self):
        return f"{self.description} (fixo)"

    @property
    def day(self):
        """Day of the month the bill falls on."""
        return self.start_date.day


class InvestmentGoalQuerySet(ScopedQuerySet):
    def with_invested(self):
        """Annotate each goal with the sum of its contributions (avoids N+1)."""
        return self.annotate(
            invested_total=Coalesce(
                models.Sum("contributions__amount"),
                models.Value(Decimal("0")),
            )
        )


class InvestmentGoal(NameTrimMixin, models.Model):
    """A savings/investment target with a goal amount, personal or shared."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="investment_goals",
    )
    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="investment_goals",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=80)
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    target_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = InvestmentGoalQuerySet.as_manager()

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def invested(self):
        """Total contributed so far. Uses the annotation from with_invested() if present."""
        if hasattr(self, "invested_total"):
            return self.invested_total
        total = self.contributions.aggregate(total=models.Sum("amount"))["total"]
        return total or Decimal("0")

    @property
    def progress(self):
        """Percentage of the target reached, capped at 100."""
        if not self.target_amount:
            return 0
        pct = self.invested / self.target_amount * 100
        return min(round(pct), 100)


class InvestmentContribution(models.Model):
    """A single deposit toward an investment goal."""

    goal = models.ForeignKey(
        InvestmentGoal,
        on_delete=models.CASCADE,
        related_name="contributions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contributions",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.amount} → {self.goal.name}"


class HouseholdList(NameTrimMixin, models.Model):
    """A named checklist that belongs to a household (group only)."""

    household = models.ForeignKey(
        Household,
        on_delete=models.CASCADE,
        related_name="lists",
    )
    name = models.CharField(max_length=80)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class HouseholdListItem(models.Model):
    """A single entry inside a household list."""

    list = models.ForeignKey(
        HouseholdList,
        on_delete=models.CASCADE,
        related_name="items",
    )
    text = models.CharField(max_length=200)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_done", "created_at"]

    def __str__(self):
        return self.text
