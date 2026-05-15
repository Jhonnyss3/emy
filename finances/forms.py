from django import forms

from .models import Category, Profile, Transaction


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
