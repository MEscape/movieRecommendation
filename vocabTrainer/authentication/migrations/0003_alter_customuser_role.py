# Generated by Django 5.1.2 on 2024-10-31 13:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0002_customuser_role"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="role",
            field=models.CharField(
                choices=[
                    ("admin", "Admin"),
                    ("user", "User"),
                    ("teacher", "Teacher"),
                    ("student", "Student"),
                    ("guest", "Guest"),
                ],
                default="user",
                max_length=10,
            ),
        ),
    ]
