# Generated by Django 2.2.4 on 2020-10-09 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('businessGroup', '0008_auto_20201001_1358'),
    ]

    operations = [
        migrations.AddField(
            model_name='batch',
            name='batch_notification',
            field=models.BooleanField(default=False),
        ),
    ]
