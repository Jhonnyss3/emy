from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models


class TransactionType(models.TextChoices):
    """Whether money comes in or goes out."""

    INCOME = "income", "Income"
    EXPENSE = "expense", "Expense"


class PaymentMethod(models.TextChoices):
    """How a transaction was settled."""

    CASH = "cash", "Cash"
    DEBIT_CARD = "debit_card", "Debit card"
    CREDIT_CARD = "credit_card", "Credit card"
    PIX = "pix", "Pix"
    BANK_SLIP = "bank_slip", "Bank slip"
    BANK_TRANSFER = "bank_transfer", "Bank transfer"


hex_color_validator = RegexValidator(
    regex=r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$",
    message="Color must be a hex value like #1abc9c.",
)


class Category(models.Model):
    """A user-defined bucket that classifies transactions."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    name = models.CharField(max_length=80)
    type = models.CharField(max_length=10, choices=TransactionType.choices)
    color = models.CharField(
        max_length=7,
        default="#3498db",
        validators=[hex_color_validator],
    )
    icon = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "name", "type"],
                name="unique_category_per_user",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"

    def clean(self):
        super().clean()
        if self.name:
            self.name = self.name.strip()
        if not self.name:
            raise ValidationError({"name": "Name cannot be blank."})


class Transaction(models.Model):
    """A single income or expense entry owned by a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="transactions",
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

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

    def clean(self):
        super().clean()
        if self.description:
            self.description = self.description.strip()

        # The category must belong to the same user as the transaction.
        if self.category_id and self.user_id:
            if self.category.user_id != self.user_id:
                raise ValidationError(
                    {"category": "Category must belong to the same user."}
                )

        # The category type must match the transaction type.
        if self.category_id and self.type:
            if self.category.type != self.type:
                raise ValidationError(
                    {
                        "category": (
                            "Category type "
                            f"'{self.category.get_type_display()}' does not "
                            f"match transaction type '{self.get_type_display()}'."
                        )
                    }
                )
