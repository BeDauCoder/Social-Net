# Generated by Django 5.1.2 on 2024-11-09 03:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web_social", "0003_alter_post_privacy"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="deletion_requested_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
