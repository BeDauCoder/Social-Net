# Generated by Django 5.1.2 on 2024-11-17 02:56

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web_social", "0010_tag"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="page",
            name="editors",
            field=models.ManyToManyField(
                blank=True,
                null=True,
                related_name="editable_pages",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
