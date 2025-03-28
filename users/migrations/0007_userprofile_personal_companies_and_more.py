# Generated by Django 5.1 on 2024-11-04 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datahub', '0011_remove_company_owner_remove_contact_owner_and_more'),
        ('users', '0006_rename_company_usercompany_alter_usercompany_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='personal_companies',
            field=models.ManyToManyField(blank=True, related_name='users_with_company_access', to='datahub.company'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='personal_contacts',
            field=models.ManyToManyField(blank=True, related_name='users_with_contact_access', to='datahub.contact'),
        ),
    ]
