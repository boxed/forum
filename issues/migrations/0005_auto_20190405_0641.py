# Generated by Django 2.1.2 on 2019-04-05 06:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('issues', '0004_auto_20190405_0627'),
    ]

    operations = [
        migrations.CreateModel(
            name='LongTextProperty',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('data', models.TextField()),
                ('time_created', models.DateTimeField(auto_now_add=True)),
                ('last_changed_time', models.DateTimeField(auto_now=True)),
                ('issue', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='long_text_properties', to='issues.Issue')),
                ('last_changed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='textproperty',
            name='data',
            field=models.CharField(db_index=True, max_length=255),
        ),
    ]
