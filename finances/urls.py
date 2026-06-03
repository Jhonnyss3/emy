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
    path("investments/", views.investment_list, name="investment_list"),
    path("investments/new/", views.investment_create, name="investment_create"),
    path(
        "investments/<int:pk>/",
        views.investment_detail,
        name="investment_detail",
    ),
    path(
        "investments/<int:pk>/edit/",
        views.investment_update,
        name="investment_update",
    ),
    path(
        "investments/<int:pk>/delete/",
        views.investment_delete,
        name="investment_delete",
    ),
    path(
        "investments/<int:pk>/contributions/add/",
        views.contribution_create,
        name="contribution_create",
    ),
    path(
        "investments/<int:pk>/contributions/<int:contrib_pk>/delete/",
        views.contribution_delete,
        name="contribution_delete",
    ),
    path("lists/", views.list_index, name="list_index"),
    path("lists/new/", views.list_create, name="list_create"),
    path("lists/<int:pk>/", views.list_detail, name="list_detail"),
    path("lists/<int:pk>/delete/", views.list_delete, name="list_delete"),
    path(
        "lists/<int:pk>/items/add/",
        views.list_item_add,
        name="list_item_add",
    ),
    path(
        "lists/<int:pk>/items/<int:item_pk>/toggle/",
        views.list_item_toggle,
        name="list_item_toggle",
    ),
    path(
        "lists/<int:pk>/items/<int:item_pk>/delete/",
        views.list_item_delete,
        name="list_item_delete",
    ),
]
