from django.contrib import admin

from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "user", "color", "is_active", "created_at")
    list_filter = ("type", "is_active", "created_at")
    search_fields = ("name", "user__username")
    autocomplete_fields = ("user",)
    ordering = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "amount",
        "type",
        "category",
        "payment_method",
        "date",
        "user",
    )
    list_filter = ("type", "payment_method", "date", "category")
    search_fields = ("description", "notes", "user__username")
    autocomplete_fields = ("user", "category")
    date_hierarchy = "date"
    ordering = ("-date",)
