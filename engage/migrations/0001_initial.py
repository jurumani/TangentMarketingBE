# Generated by Django 5.1 on 2024-11-12 18:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('datahub', '0011_remove_company_owner_remove_contact_owner_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('communication_type', models.CharField(choices=[('email', 'Email'), ('sms', 'SMS'), ('whatsapp', 'WhatsApp')], max_length=50)),
                ('scheduled_date', models.DateTimeField(blank=True, help_text='Date to automatically start the campaign.', null=True)),
                ('is_manual_start', models.BooleanField(default=False, help_text='Indicates if the campaign should be started manually.')),
                ('started_at', models.DateTimeField(blank=True, help_text='Timestamp of when the campaign was started.', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CampaignContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(default='pending', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campaign_contacts', to='engage.campaign')),
                ('contact', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='campaigns', to='datahub.contact')),
            ],
        ),
        migrations.CreateModel(
            name='CampaignMessage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(blank=True, max_length=255, null=True)),
                ('body', models.TextField()),
                ('media_url', models.URLField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='engage.campaign')),
            ],
        ),
    ]
