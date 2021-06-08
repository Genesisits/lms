# Generated by Django 2.2.4 on 2020-02-03 03:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('businessGroup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('baseclass_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='businessGroup.BaseClass')),
                ('attendances', models.CharField(blank=True, choices=[('absent', 'Absent'), ('present', 'Present')], max_length=8)),
                ('schedule', models.DateField()),
                ('batches', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='batch_attend', to='businessGroup.Batch')),
            ],
            bases=('businessGroup.baseclass',),
        ),
    ]