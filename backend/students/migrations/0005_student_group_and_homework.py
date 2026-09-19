from django.db import migrations, models


def convert_sections_to_groups(apps, schema_editor):
    Student = apps.get_model("students", "Student")

    for student in Student.objects.all():
        if student.student_class in ["LKG", "UKG"]:
            group = "ClassE"
        elif student.student_class in ["1", "2", "3"]:
            group = "ClassA"
        elif student.student_class in ["4", "5", "6"]:
            group = "ClassB"
        elif student.student_class in ["7", "8"]:
            group = "ClassC"
        elif student.student_class in ["9", "10"]:
            group = "ClassD"
        else:
            group = "ClassE"

        student.section = group
        student.save(update_fields=["section"])
        
def create_student_homework_table(apps, schema_editor):
    from students.models import StudentHomework

    table_name = StudentHomework._meta.db_table

    existing_tables = (
        schema_editor.connection.introspection.table_names()
    )

    if table_name not in existing_tables:
        schema_editor.create_model(StudentHomework)
        
class Migration(migrations.Migration):

    dependencies = [
        ("admin2", "0004_volunteerassignment_homework_attachment_and_more"),
        ("students", "0004_student_section"),
        ("teachers", "0005_studentprogress"),
    ]

    operations = [
        migrations.AlterField(
            model_name="student",
            name="section",
            field=models.CharField(
                choices=[
                    ("ClassA", "Class A"),
                    ("ClassB", "Class B"),
                    ("ClassC", "Class C"),
                    ("ClassD", "Class D"),
                    ("ClassE", "Class E"),
                ],
                max_length=20,
                null=True,
                blank=True,
            ),
        ),

        migrations.RunPython(
            convert_sections_to_groups,
            migrations.RunPython.noop,
        ),

        migrations.AlterField(
            model_name="student",
            name="section",
            field=models.CharField(
                choices=[
                    ("ClassA", "Class A"),
                    ("ClassB", "Class B"),
                    ("ClassC", "Class C"),
                    ("ClassD", "Class D"),
                    ("ClassE", "Class E"),
                ],
                max_length=20,
            ),
        ),

        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
            create_student_homework_table,
                 migrations.RunPython.noop,
        ),
        ],
            state_operations=[
                migrations.CreateModel(
                    name="StudentHomework",
                    fields=[
                        (
                            "id",
                            models.BigAutoField(
                                auto_created=True,
                                primary_key=True,
                                serialize=False,
                                verbose_name="ID",
                            ),
                        ),
                        (
                            "status",
                            models.CharField(
                                choices=[
                                    ("PENDING", "Pending"),
                                    ("COMPLETED", "Completed"),
                                ],
                                default="PENDING",
                                max_length=20,
                            ),
                        ),
                        (
                            "completed_at",
                            models.DateTimeField(
                                blank=True,
                                null=True,
                            ),
                        ),
                        (
                            "created_at",
                            models.DateTimeField(
                                auto_now_add=True,
                            ),
                        ),
                        (
                            "updated_at",
                            models.DateTimeField(
                                auto_now=True,
                            ),
                        ),
                        (
                            "assignment",
                            models.ForeignKey(
                                on_delete=models.PROTECT,
                                related_name="student_homework_records",
                                to="admin2.volunteerassignment",
                            ),
                        ),
                        (
                            "student",
                            models.ForeignKey(
                                on_delete=models.PROTECT,
                                related_name="homework_records",
                                to="students.student",
                            ),
                        ),
                        (
                            "work_session",
                            models.ForeignKey(
                                on_delete=models.PROTECT,
                                related_name="student_homework_records",
                                to="teachers.volunteerworksession",
                            ),
                        ),
                    ],
                    options={
                        "ordering": ["-updated_at"],
                        "constraints": [
                            models.UniqueConstraint(
                                fields=("student", "assignment"),
                                name="unique_student_homework_per_assignment",
                            ),
                        ],
                    },
                ),
            ],
        ),
    ]