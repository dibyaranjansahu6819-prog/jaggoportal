from django.db import migrations


def ensure_student_homework_table(apps, schema_editor):
    StudentHomework = apps.get_model(
        "students",
        "StudentHomework",
    )

    connection = schema_editor.connection
    table_name = StudentHomework._meta.db_table

    print(f"\n[0009] Checking table: {table_name}")

    existing_tables = connection.introspection.table_names()

    print(f"[0009] Table exists before create: {table_name in existing_tables}")

    if table_name not in existing_tables:
        print("[0009] Creating StudentHomework table...")
        schema_editor.create_model(StudentHomework)
        print("[0009] create_model() completed.")

        existing_tables_after = connection.introspection.table_names()

        print(
            "[0009] Table exists after create: "
            f"{table_name in existing_tables_after}"
        )
    else:
        print("[0009] StudentHomework table already exists. Skipping create.")


class Migration(migrations.Migration):

    dependencies = [
        (
            "students",
            "0008_alter_studentxptransaction_source",
        ),
    ]

    operations = [
        migrations.RunPython(
            ensure_student_homework_table,
            migrations.RunPython.noop,
        ),
    ]