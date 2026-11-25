from django.contrib import admin

from .models import AppSettings, Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "user", "is_default")
    list_filter = ("kind", "is_default", "user")
    search_fields = ("name", "user__email")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "description", "kind", "category", "amount", "payment_method", "user")
    list_filter = ("kind", "category", "payment_method", "date", "user")
    search_fields = ("description", "user__email")
    date_hierarchy = "date"


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "currency")
