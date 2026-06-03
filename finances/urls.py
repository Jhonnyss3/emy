from django.urls import path

from . import views

app_name = "finances"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("profile/", views.profile_edit, name="profile_edit"),
    path("scope/switch/", views.scope_switch, name="scope_switch"),
    path("groups/", views.household_list, name="household_list"),
    path("groups/new/", views.household_create, name="household_create"),
    path("groups/<int:pk>/", views.household_detail, name="household_detail"),
    path(
        "groups/<int:pk>/members/add/",
        views.member_add,
        name="member_add",
    ),
    path(
        "groups/<int:pk>/members/<int:user_id>/remove/",
        views.member_remove,
        name="member_remove",
    ),
    path("transactions/", views.transaction_list, name="transaction_list"),
    path("transactions/new/", views.transaction_create, name="transaction_create"),
    path(
        "transactions/<int:pk>/edit/",
        views.transaction_update,
        name="transaction_update",
    ),
    path(
        "transactions/<int:pk>/delete/",
        views.transaction_delete,
        name="transaction_delete",
    ),
    path("categories/", views.category_list, name="category_list"),
    path("categories/new/", views.category_create, name="category_create"),
    path(
        "categories/<int:pk>/edit/",
        views.category_update,
        name="category_update",
    ),
    path(
        "categories/<int:pk>/delete/",
        views.category_delete,
        name="category_delete",
    ),
]
