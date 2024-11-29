# Generated by Django 5.1.2 on 2024-11-21 15:51

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web_social", "0013_message_is_read_alter_message_timestamp"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="likes",
            field=models.ManyToManyField(
                blank=True, related_name="liked_pages", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]