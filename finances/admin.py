from django.contrib import admin

from .models import (
    Category,
    Household,
    HouseholdList,
    HouseholdListItem,
    HouseholdMembership,
    InvestmentContribution,
    InvestmentGoal,
    Transaction,
)


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


class InvestmentContributionInline(admin.TabularInline):
    model = InvestmentContribution
    extra = 0
    autocomplete_fields = ("user",)


@admin.register(InvestmentGoal)
class InvestmentGoalAdmin(admin.ModelAdmin):
    list_display = ("name", "target_amount", "target_date", "user", "household", "is_active")
    list_filter = ("is_active", "household", "target_date")
    search_fields = ("name", "user__username")
    autocomplete_fields = ("user", "household")
    inlines = (InvestmentContributionInline,)
    ordering = ("name",)


@admin.register(InvestmentContribution)
class InvestmentContributionAdmin(admin.ModelAdmin):
    list_display = ("goal", "amount", "date", "user")
    list_filter = ("date",)
    search_fields = ("goal__name", "user__username")
    autocomplete_fields = ("goal", "user")
    date_hierarchy = "date"
    ordering = ("-date",)


class HouseholdListItemInline(admin.TabularInline):
    model = HouseholdListItem
    extra = 0


@admin.register(HouseholdList)
class HouseholdListAdmin(admin.ModelAdmin):
    list_display = ("name", "household", "created_at")
    list_filter = ("household",)
    search_fields = ("name", "household__name")
    autocomplete_fields = ("household",)
    inlines = (HouseholdListItemInline,)
    ordering = ("name",)
