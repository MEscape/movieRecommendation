# Generated by Django 5.1.2 on 2024-10-31 12:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="customuser",
            name="role",
            field=models.CharField(
                choices=[("admin", "Admin"), ("user", "User"), ("guest", "Guest")],
                default="user",
                max_length=10,
            ),
        ),
    ]
