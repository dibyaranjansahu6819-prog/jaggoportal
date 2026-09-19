from django.db import migrations, models


def rename_section_to_group(apps, schema_editor):
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'students_student'
            AND column_name IN ('section', 'group')
            """
        )

        columns = {row[0] for row in cursor.fetchall()}

        # Fresh database:
        # section exists and group does not exist.
        if "section" in columns and "group" not in columns:
            cursor.execute(
                """
                ALTER TABLE "students_student"
                RENAME COLUMN "section" TO "group"
                """
            )

        # Existing database:
        # group already exists, so nothing needs to be changed.


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0005_student_group_and_homework"),
    ]

    operations = [
        migrations.RunPython(
            rename_section_to_group,
            migrations.RunPython.noop,
        ),

        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RenameField(
                    model_name="student",
                    old_name="section",
                    new_name="group",
                ),
                migrations.AlterField(
                    model_name="student",
                    name="group",
                    field=models.CharField(
                        choices=[
                            ("ClassA", "ClassA"),
                            ("ClassB", "ClassB"),
                            ("ClassC", "ClassC"),
                            ("ClassD", "ClassD"),
                            ("ClassE", "ClassE"),
                        ],
                        editable=False,
                        max_length=20,
                    ),
                ),
            ],
        ),
    ]