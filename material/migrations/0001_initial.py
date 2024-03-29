# Generated by Django 2.2.4 on 2020-02-03 03:01

from django.db import migrations, models
import django.db.models.deletion
import material.validations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('businessGroup', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='FieldStudyObservation',
            fields=[
                ('baseclass_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='businessGroup.BaseClass')),
                ('lab_name', models.CharField(max_length=150)),
                ('file', models.FileField(upload_to='media/')),
                ('score', models.DecimalField(decimal_places=2, default='0', max_digits=5)),
            ],
            bases=('businessGroup.baseclass',),
        ),
        migrations.CreateModel(
            name='Material',
            fields=[
                ('baseclass_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='businessGroup.BaseClass')),
                ('file', models.FileField(upload_to='', validators=[material.validations.validate_file_extension])),
                ('comment', models.CharField(blank=True, max_length=255, null=True)),
                ('file_status', models.CharField(choices=[('PENDING', 'pending'), ('APPROVED', 'approved'), ('REJECTED', 'rejected')], default='pending', max_length=15)),
                ('as_batch', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='businessGroup.Batch')),
                ('as_module', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='businessGroup.Module')),
            ],
            bases=('businessGroup.baseclass',),
        ),
    ]
