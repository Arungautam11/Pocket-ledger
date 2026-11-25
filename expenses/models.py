from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.conf import settings


class Category(models.Model):
    EXPENSE = "expense"
    INCOME = "income"
    TYPES = [(EXPENSE, "Expense"), (INCOME, "Income")]
    name = models.CharField(max_length=40)
    kind = models.CharField(max_length=8, choices=TYPES)
    is_default = models.BooleanField(default=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="categories")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [models.UniqueConstraint(fields=["user", "name", "kind"], name="unique_user_category_name_kind")]

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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    date = models.DateField()
    description = models.CharField(max_length=120)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="transactions")
    payment_method = models.CharField(max_length=8, choices=PAYMENT_METHODS, default=OTHER)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "-id"]
        indexes = [models.Index(fields=["user", "date"], name="expense_user_date_idx")]

    def clean(self):
        super().clean()
        if self.category_id and self.user_id:
            if self.category.user_id != self.user_id:
                raise ValidationError({"category": "Choose one of your own categories."})
            if self.category.kind != self.kind:
                raise ValidationError({"category": "Choose a category for this transaction type."})


class AppSettings(models.Model):
    CURRENCIES = [
        ("INR", "INR · ₹ Indian rupee"),
        ("USD", "USD · $ US dollar"),
        ("EUR", "EUR · € Euro"),
        ("GBP", "GBP · £ Pound sterling"),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCIES, default="INR")
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="app_settings")

    @classmethod
    def current(cls, user):
        settings, _ = cls.objects.get_or_create(user=user)
        return settings
