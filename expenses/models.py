from django.core.validators import MinValueValidator
from django.db import models


class Category(models.Model):
    EXPENSE = "expense"
    INCOME = "income"
    TYPES = [(EXPENSE, "Expense"), (INCOME, "Income")]
    name = models.CharField(max_length=40)
    kind = models.CharField(max_length=8, choices=TYPES)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["name", "kind"], name="unique_category_name_kind")]

    def __str__(self):
        return self.name


class Transaction(models.Model):
    EXPENSE = "expense"
    INCOME = "income"
    TYPES = [(EXPENSE, "Expense"), (INCOME, "Income")]
    CASH = "cash"
    CARD = "card"
    UPI = "upi"
    BANK = "bank"
    OTHER = "other"
    PAYMENT_METHODS = [(CASH, "Cash"), (CARD, "Card"), (UPI, "UPI"), (BANK, "Bank transfer"), (OTHER, "Other")]

    kind = models.CharField(max_length=8, choices=TYPES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateField()
    description = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")
    payment_method = models.CharField(max_length=8, choices=PAYMENT_METHODS, default=OTHER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]


class AppSettings(models.Model):
    CURRENCIES = [
        ("INR", "INR · ₹ Indian rupee"),
        ("USD", "USD · $ US dollar"),
        ("EUR", "EUR · € Euro"),
        ("GBP", "GBP · £ Pound sterling"),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="INR")

    @classmethod
    def current(cls):
        settings, _ = cls.objects.get_or_create(pk=1)
        return settings
