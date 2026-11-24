from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


def add_default_categories(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    defaults = {
        "expense": ["Food", "Grocery", "Shopping", "Transportation", "Rent", "Electricity", "Medical", "Entertainment", "Education", "Other"],
        "income": ["Salary", "Business", "Freelance", "Investment", "Other"],
    }
    for kind, names in defaults.items():
        Category.objects.bulk_create([Category(name=name, kind=kind, is_default=True) for name in names])


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="AppSettings",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("currency", models.CharField(choices=[("INR", "INR · ₹ Indian rupee"), ("USD", "USD · $ US dollar"), ("EUR", "EUR · € Euro"), ("GBP", "GBP · £ Pound sterling")], default="INR", max_length=3))],
        ),
        migrations.CreateModel(
            name="Category",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("name", models.CharField(max_length=40)), ("kind", models.CharField(choices=[("expense", "Expense"), ("income", "Income")], max_length=8)), ("is_default", models.BooleanField(default=False))],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("kind", models.CharField(choices=[("expense", "Expense"), ("income", "Income")], max_length=8)), ("amount", models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0.01)])), ("date", models.DateField()), ("description", models.CharField(max_length=120)), ("payment_method", models.CharField(choices=[("cash", "Cash"), ("card", "Card"), ("upi", "UPI"), ("bank", "Bank transfer"), ("other", "Other")], default="other", max_length=8)), ("created_at", models.DateTimeField(auto_now_add=True)), ("category", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="transactions", to="expenses.category"))],
            options={"ordering": ["-date", "-id"]},
        ),
        migrations.AddConstraint(model_name="category", constraint=models.UniqueConstraint(fields=("name", "kind"), name="unique_category_name_kind")),
        migrations.RunPython(add_default_categories, migrations.RunPython.noop),
    ]
