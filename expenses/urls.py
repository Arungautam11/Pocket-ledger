from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("transactions/", views.transaction_list, name="transactions"),
    path("expenses/", views.transaction_list, {"kind": "expense"}, name="expenses"),
    path("income/", views.transaction_list, {"kind": "income"}, name="income"),
    path("expenses/add/", views.transaction_form, {"kind": "expense"}, name="expense_add"),
    path("income/add/", views.transaction_form, {"kind": "income"}, name="income_add"),
    path("expenses/<int:transaction_id>/edit/", views.transaction_form, {"kind": "expense"}, name="expense_edit"),
    path("income/<int:transaction_id>/edit/", views.transaction_form, {"kind": "income"}, name="income_edit"),
    path("transactions/<int:transaction_id>/delete/", views.transaction_delete, name="transaction_delete"),
    path("reports/", views.reports, name="reports"),
    path("reports/export/", views.export_csv, name="export_csv"),
    path("categories/", views.categories, name="categories"),
    path("categories/<int:category_id>/edit/", views.categories, name="category_edit"),
    path("categories/<int:category_id>/delete/", views.category_delete, name="category_delete"),
    path("settings/", views.settings_page, name="settings"),
]
