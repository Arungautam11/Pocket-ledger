from django.conf import settings
from django.db import migrations


INDEX_NAME = "accounts_user_email_ci_uniq"


def create_email_index(apps, schema_editor):
    app_label, model_name = settings.AUTH_USER_MODEL.split(".")
    User = apps.get_model(app_label, model_name)
    table = schema_editor.quote_name(User._meta.db_table)
    email_column = schema_editor.quote_name(User._meta.get_field("email").column)
    schema_editor.execute(
        f"CREATE UNIQUE INDEX {schema_editor.quote_name(INDEX_NAME)} "
        f"ON {table} (LOWER({email_column}))"
    )


def drop_email_index(apps, schema_editor):
    schema_editor.execute(f"DROP INDEX {schema_editor.quote_name(INDEX_NAME)}")


class Migration(migrations.Migration):
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [migrations.RunPython(create_email_index, drop_email_index)]
