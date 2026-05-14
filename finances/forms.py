from django import forms

from .models import Category, Transaction


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ("name", "type", "color", "icon", "is_active")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Groceries"}),
            "type": forms.Select(),
            "color": forms.TextInput(attrs={"type": "color"}),
            "icon": forms.TextInput(attrs={"placeholder": "Optional icon name"}),
        }


class TransactionForm(forms.ModelForm):
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

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        # Only let the user pick their own active categories.
        if user is not None:
            self.fields["category"].queryset = Category.objects.filter(
                user=user, is_active=True
            )

    def clean(self):
        cleaned_data = super().clean()
        # Attach the owner before model.clean() runs the cross-field checks.
        if self.user is not None:
            self.instance.user = self.user
        return cleaned_data
