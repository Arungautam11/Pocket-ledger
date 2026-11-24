from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AppSettings, Category, Transaction


class LedgerWorkflowTests(TestCase):
    def setUp(self):
        self.food = Category.objects.create(name="Food", kind="expense", is_default=True)
        self.salary = Category.objects.create(name="Salary", kind="income", is_default=True)

    def test_dashboard_loads_with_month_summary(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total balance")

    def test_create_expense_and_reject_negative_amount(self):
        data = {"kind": "expense", "description": "Lunch", "amount": "12.50", "date": timezone.localdate().isoformat(), "category": self.food.pk, "payment_method": "upi"}
        response = self.client.post(reverse("expense_add"), data)
        self.assertRedirects(response, reverse("expenses"))
        self.assertEqual(Transaction.objects.get().amount, Decimal("12.50"))
        data["amount"] = "-1"
        response = self.client.post(reverse("expense_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Transaction.objects.count(), 1)

    def test_edit_and_delete_transaction(self):
        transaction = Transaction.objects.create(kind="expense", description="Coffee", amount="4.00", date=timezone.localdate(), category=self.food, payment_method="cash")
        response = self.client.post(reverse("expense_edit", args=[transaction.pk]), {"kind": "expense", "description": "Tea", "amount": "3.50", "date": timezone.localdate().isoformat(), "category": self.food.pk, "payment_method": "cash"})
        self.assertRedirects(response, reverse("expenses"))
        transaction.refresh_from_db()
        self.assertEqual(transaction.description, "Tea")
        response = self.client.post(reverse("transaction_delete", args=[transaction.pk]))
        self.assertRedirects(response, reverse("expenses"))
        self.assertFalse(Transaction.objects.exists())

    def test_income_and_reports_csv(self):
        Transaction.objects.create(kind="income", description="Pay", amount="100.00", date=timezone.localdate(), category=self.salary, payment_method="bank")
        report = self.client.get(reverse("reports"), {"period": "month"})
        self.assertEqual(report.status_code, 200)
        export = self.client.get(reverse("export_csv"), {"period": "month"})
        self.assertEqual(export["Content-Type"], "text/csv")
        self.assertIn(b"Pay", export.content)

    def test_currency_preference_is_saved(self):
        AppSettings.current()
        response = self.client.post(reverse("settings"), {"currency": "USD"})
        self.assertRedirects(response, reverse("settings"))
        self.assertEqual(AppSettings.current().currency, "USD")
