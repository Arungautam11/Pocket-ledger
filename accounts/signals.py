from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver


EXPENSE_CATEGORIES = (
    "Food", "Grocery", "Shopping", "Transportation", "Rent", "Electricity",
    "Medical", "Entertainment", "Education", "Other",
)
INCOME_CATEGORIES = ("Salary", "Business", "Freelance", "Investment", "Other")


@receiver(post_save, sender=get_user_model())
def create_user_defaults(sender, instance, created, **kwargs):
    if not created:
        return
    from expenses.models import AppSettings, Category

    Category.objects.bulk_create(
        [Category(user=instance, name=name, kind=kind, is_default=True)
         for kind, names in (("expense", EXPENSE_CATEGORIES), ("income", INCOME_CATEGORIES))
         for name in names]
    )
    AppSettings.objects.create(user=instance)
