# Generated by Django 5.1 on 2024-09-08 18:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0002_message_is_system_message_alter_message_sender'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='actions',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='message_type',
            field=models.CharField(choices=[('informational', 'Informational'), ('actionable', 'Actionable')], default='informational', max_length=50),
        ),
    ]
