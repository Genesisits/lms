# Generated by Django 2.2.4 on 2020-02-03 03:01

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('businessGroup', '0002_auto_20200203_0831'),
        ('assessment', '0002_auto_20200203_0831'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('material', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='material',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='materialuser', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='fieldstudyobservation',
            name='assessment_is',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='field', to='assessment.BatchAssessment'),
        ),
        migrations.AddField(
            model_name='fieldstudyobservation',
            name='batch',
            field=models.ManyToManyField(related_name='field_study', to='businessGroup.Batch'),
        ),
        migrations.AddField(
            model_name='fieldstudyobservation',
            name='trainee',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='obs_trainee', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='fieldstudyobservation',
            name='trainer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='obs_trainer', to=settings.AUTH_USER_MODEL),
        ),
    ]
