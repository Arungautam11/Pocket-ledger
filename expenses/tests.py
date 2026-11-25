from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AppSettings, Category, Transaction


class LedgerWorkflowTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="owner@example.com", email="owner@example.com", password="Safe-passphrase-981!",
            first_name="Owner",
        )
        self.other = User.objects.create_user(
            username="other@example.com", email="other@example.com", password="Safe-passphrase-982!",
            first_name="Other",
        )
        self.client.force_login(self.user)
        self.food = Category.objects.get(user=self.user, name="Food", kind="expense")
        self.salary = Category.objects.get(user=self.user, name="Salary", kind="income")
        self.other_food = Category.objects.get(user=self.other, name="Food", kind="expense")

    def make_transaction(self, user=None, category=None, **kwargs):
        return Transaction.objects.create(
            user=user or self.user,
            kind=kwargs.pop("kind", "expense"),
            description=kwargs.pop("description", "Lunch"),
            amount=kwargs.pop("amount", "12.50"),
            date=kwargs.pop("date", timezone.localdate()),
            category=category or self.food,
            payment_method=kwargs.pop("payment_method", "upi"),
            **kwargs,
        )

    def test_dashboard_loads_with_user_specific_month_summary(self):
        self.make_transaction(description="My lunch", amount="12.50")
        self.make_transaction(user=self.other, category=self.other_food, description="Other lunch", amount="900.00")
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total balance")
        self.assertContains(response, "My lunch")
        self.assertNotContains(response, "Other lunch")
        self.assertContains(response, "12.50")
        self.assertNotContains(response, "900.00")

    def test_create_expense_and_reject_negative_amount(self):
        data = {"kind": "expense", "description": "Lunch", "amount": "12.50", "date": timezone.localdate().isoformat(), "category": self.food.pk, "payment_method": "upi"}
        response = self.client.post(reverse("expense_add"), data)
        self.assertRedirects(response, reverse("expenses"))
        transaction = Transaction.objects.get()
        self.assertEqual(transaction.amount, Decimal("12.50"))
        self.assertEqual(transaction.user, self.user)
        data["amount"] = "-1"
        response = self.client.post(reverse("expense_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_foreign_category_cannot_be_used_in_transaction(self):
        response = self.client.post(reverse("expense_add"), {
            "kind": "expense", "description": "Forged", "amount": "1.00",
            "date": timezone.localdate().isoformat(), "category": self.other_food.pk,
            "payment_method": "cash",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Transaction.objects.exists())

    def test_edit_and_delete_transaction(self):
        transaction = self.make_transaction(description="Coffee", amount="4.00", payment_method="cash")
        response = self.client.post(reverse("expense_edit", args=[transaction.pk]), {"kind": "expense", "description": "Tea", "amount": "3.50", "date": timezone.localdate().isoformat(), "category": self.food.pk, "payment_method": "cash"})
        self.assertRedirects(response, reverse("expenses"))
        transaction.refresh_from_db()
        self.assertEqual(transaction.description, "Tea")
        response = self.client.post(reverse("transaction_delete", args=[transaction.pk]))
        self.assertRedirects(response, reverse("expenses"))
        self.assertFalse(Transaction.objects.exists())

    def test_user_cannot_view_edit_or_delete_another_users_transaction(self):
        foreign = self.make_transaction(user=self.other, category=self.other_food, description="Private record")
        response = self.client.get(reverse("transactions"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Private record")
        self.assertEqual(self.client.get(reverse("expense_edit", args=[foreign.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("transaction_delete", args=[foreign.pk])).status_code, 404)
        self.assertTrue(Transaction.objects.filter(pk=foreign.pk).exists())

    def test_user_cannot_access_another_users_category(self):
        foreign = self.other_food
        self.assertEqual(self.client.get(reverse("category_edit", args=[foreign.pk])).status_code, 404)
        self.assertEqual(self.client.post(reverse("category_delete", args=[foreign.pk])).status_code, 404)
        self.assertTrue(Category.objects.filter(pk=foreign.pk).exists())

    def test_income_reports_and_csv_are_user_specific(self):
        own = self.make_transaction(kind="income", category=self.salary, description="My pay", amount="100.00")
        self.make_transaction(user=self.other, category=self.other_food, description="Other private", amount="500.00")
        report = self.client.get(reverse("reports"), {"period": "month"})
        self.assertEqual(report.status_code, 200)
        self.assertContains(report, "My pay")
        self.assertNotContains(report, "Other private")
        export = self.client.get(reverse("export_csv"), {"period": "month"})
        self.assertEqual(export["Content-Type"], "text/csv")
        self.assertIn(b"My pay", export.content)
        self.assertNotIn(b"Other private", export.content)
        self.assertTrue(Transaction.objects.filter(pk=own.pk, user=self.user).exists())

    def test_currency_preference_is_saved_per_user(self):
        prefs = AppSettings.current(self.user)
        response = self.client.post(reverse("settings"), {"currency": "USD"})
        self.assertRedirects(response, reverse("settings"))
        prefs.refresh_from_db()
        self.assertEqual(prefs.currency, "USD")
        self.assertEqual(AppSettings.current(self.other).currency, "INR")

    def test_category_names_are_unique_per_user_and_type(self):
        duplicate = self.client.post(reverse("categories"), {"name": "food", "kind": "expense"})
        self.assertEqual(duplicate.status_code, 200)
        self.assertEqual(Category.objects.filter(user=self.user, name__iexact="food", kind="expense").count(), 1)
        self.assertEqual(Category.objects.filter(user=self.other, name="Food", kind="expense").count(), 1)
