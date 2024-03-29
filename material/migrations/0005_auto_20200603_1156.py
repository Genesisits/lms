# Generated by Django 2.2.4 on 2020-06-03 06:26

from django.db import migrations, models
import material.validations


class Migration(migrations.Migration):

    dependencies = [
        ('material', '0004_auto_20200402_1138'),
    ]

    operations = [
        migrations.AlterField(
            model_name='material',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='', validators=[material.validations.validate_file_extension]),
        ),
        migrations.AlterField(
            model_name='material',
            name='file_status',
            field=models.CharField(choices=[('IN PROGRESS', 'in progress'), ('INITIATED', 'initiated'), ('APPROVED', 'approved'), ('PENDING', 'pending'), ('NOT APPROVED', 'not approved')], default='PENDING', max_length=15),
        ),
    ]
