# Generated by Django 2.2.4 on 2020-08-14 18:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0005_auto_20200603_1156'),
    ]

    operations = [
        migrations.AlterField(
            model_name='material',
            name='file_status',
            field=models.CharField(choices=[('IN PROGRESS', 'in progress'), ('INITIATED', 'initiated'), ('APPROVED', 'approved'), ('PENDING', 'pending'), ('NOT APPROVED', 'not approved')], default='APPROVED', max_length=15),
        ),
    ]
