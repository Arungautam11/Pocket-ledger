from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


LEGACY_OWNER_USERNAME = "arun"


def assign_existing_records(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    Transaction = apps.get_model("expenses", "Transaction")
    AppSettings = apps.get_model("expenses", "AppSettings")
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)

    has_existing_ledger = (
        Transaction.objects.exists()
        or Category.objects.filter(is_default=False).exists()
        or AppSettings.objects.exists()
    )
    if not has_existing_ledger:
        # These are only the global seed categories from the initial migration.
        Category.objects.filter(is_default=True).delete()
        return

    owners = User.objects.filter(username=LEGACY_OWNER_USERNAME)
    if owners.count() != 1:
        raise RuntimeError(
            "Existing expense data needs an owner. The approved owner username 'arun' "
            "must exist exactly once before this migration can continue. No ledger rows "
            "were assigned."
        )
    owner = owners.first()
    Category.objects.filter(user__isnull=True).update(user=owner)
    Transaction.objects.filter(user__isnull=True).update(user=owner)
    AppSettings.objects.filter(user__isnull=True).update(user=owner)


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="category",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="categories",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="category",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="transaction",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name="appsettings",
            name="user",
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="app_settings",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(assign_existing_records, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name="category",
            name="unique_category_name_kind",
        ),
        migrations.AlterField(
            model_name="category",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="categories",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name="transaction",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="appsettings",
            name="user",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="app_settings",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=("user", "name", "kind"),
                name="unique_user_category_name_kind",
            ),
        ),
        migrations.AddIndex(
            model_name="transaction",
            index=models.Index(fields=["user", "date"], name="expense_user_date_idx"),
        ),
    ]
