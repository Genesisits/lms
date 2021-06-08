# Generated by Django 2.2.4 on 2020-04-02 06:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0003_auto_20200329_1800'),
    ]

    operations = [
        migrations.AlterField(
            model_name='material',
            name='file_status',
            field=models.CharField(choices=[('IN PROGRESS', 'in progress'), ('INITIATED', 'initiated'), ('APPROVED', 'approved'), ('PENDING', 'pending'), ('NOT APPROVED', 'not approved')], default='pending', max_length=15),
        ),
    ]