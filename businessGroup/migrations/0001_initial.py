# Generated by Django 2.2.4 on 2020-02-03 03:01

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='BaseClass',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='BatchModuleActivation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('active', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Batch',
            fields=[
                ('baseclass_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='businessGroup.BaseClass')),
                ('name', models.CharField(max_length=50)),
                ('is_active', models.BooleanField(default=False)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, editable=False, null=True)),
                ('training_status', models.DecimalField(decimal_places=2, default='0', max_digits=4)),
            ],
            bases=('businessGroup.baseclass',),
        ),
        migrations.CreateModel(
            name='BusinessGroup',
            fields=[
                ('baseclass_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='businessGroup.BaseClass')),
                ('name', models.CharField(max_length=200)),
                ('days', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=False)),
            ],
            bases=('businessGroup.baseclass',),
        ),
        migrations.CreateModel(
            name='Module',
            fields=[
                ('baseclass_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='businessGroup.BaseClass')),
                ('name', models.TextField(max_length=255, unique=True)),
                ('is_active', models.BooleanField(default=False)),
            ],
            bases=('businessGroup.baseclass',),
        ),
        migrations.CreateModel(
            name='Level',
            fields=[
                ('baseclass_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='businessGroup.BaseClass')),
                ('name', models.TextField(max_length=255)),
                ('is_active', models.BooleanField(default=False)),
                ('modules', models.ManyToManyField(blank=True, to='businessGroup.Module')),
            ],
            bases=('businessGroup.baseclass',),
        ),
    ]
