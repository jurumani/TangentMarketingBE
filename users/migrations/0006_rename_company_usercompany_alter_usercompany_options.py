# Generated by Django 5.1 on 2024-09-22 09:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_company_userprofile_company'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Company',
            new_name='UserCompany',
        ),
        migrations.AlterModelOptions(
            name='usercompany',
            options={'verbose_name_plural': 'User Companies'},
        ),
    ]
