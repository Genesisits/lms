# Generated by Django 2.2.4 on 2020-10-08 14:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assessment', '0009_auto_20200815_1227'),
    ]

    operations = [
        migrations.AddField(
            model_name='multipartdata',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='multipartdata',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
