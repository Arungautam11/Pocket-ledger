from django.contrib import admin

from .models import AppSettings, Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "kind", "is_default")
    list_filter = ("kind", "is_default")
    search_fields = ("name",)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("date", "description", "kind", "category", "amount", "payment_method")
    list_filter = ("kind", "category", "payment_method", "date")
    search_fields = ("description",)
    date_hierarchy = "date"


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    list_display = ("id", "currency")
