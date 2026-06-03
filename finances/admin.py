from django.contrib import admin

from .models import Category, Household, HouseholdMembership, Transaction


class HouseholdMembershipInline(admin.TabularInline):
    model = HouseholdMembership
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(Household)
class HouseholdAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "created_at")
    search_fields = ("name", "created_by__username")
    autocomplete_fields = ("created_by",)
    inlines = (HouseholdMembershipInline,)
    ordering = ("name",)


@admin.register(HouseholdMembership)
class HouseholdMembershipAdmin(admin.ModelAdmin):
    list_display = ("household", "user", "joined_at")
    search_fields = ("household__name", "user__username")
    autocomplete_fields = ("household", "user")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "type",
        "user",
        "household",
        "color",
        "is_active",
        "created_at",
    )
    list_filter = ("type", "is_active", "household", "created_at")
    search_fields = ("name", "user__username")
    autocomplete_fields = ("user", "household")
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
        "household",
    )
    list_filter = ("type", "payment_method", "date", "category", "household")
    search_fields = ("description", "notes", "user__username")
    autocomplete_fields = ("user", "household", "category")
    date_hierarchy = "date"
    ordering = ("-date",)
