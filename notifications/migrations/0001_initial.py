# Generated by Django 2.2.4 on 2020-04-02 14:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailTemplates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=50)),
                ('body', models.CharField(max_length=1000)),
                ('purpose', models.CharField(max_length=100)),
                ('model', models.CharField(choices=[('USER', 'user'), ('MODULE', 'module'), ('LEVEL', 'level'), ('BUSINESSGROUP', 'businessgroup'), ('BATCH', 'batch'), ('ASSESSMENT', 'assessment'), ('BATCHASSESSMENT', 'batchassessment'), ('ANSWER', 'answer'), ('FEEDBACK', 'feedback'), ('ATTENDANCE', 'attendance'), ('MATERIAL', 'material'), ('FIELDSTUDY', 'fieldstudy')], max_length=12)),
            ],
        ),
        migrations.CreateModel(
            name='EmailNotifications',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.BooleanField(default=False)),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='notifications.EmailTemplates')),
                ('users', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
