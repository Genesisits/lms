# Generated by Django 2.2.4 on 2020-04-02 14:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailtemplates',
            name='body',
            field=models.TextField(max_length=1000),
        ),
    ]
