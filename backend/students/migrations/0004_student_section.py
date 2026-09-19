from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("students", "0003_remove_student_auth_user"),
    ]

    operations = [
        migrations.AddField(
            model_name="student",
            name="section",
            field=models.CharField(
                max_length=20,
                choices=[
                    ("ClassA", "ClassA"),
                    ("ClassB", "ClassB"),
                    ("ClassC", "ClassC"),
                    ("ClassD", "ClassD"),
                ],
                null=True,
                blank=True,
            ),
        ),
    ]