# Generated by Django 5.1.2 on 2024-11-29 07:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("web_social", "0015_message_is_recalled"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="is_recalled_by_sender",
            field=models.BooleanField(default=False),
        ),
    ]