# Generated by Django 2.2a1 on 2019-02-24 15:19

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('unread', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Time',
            new_name='UserTime',
        ),
        migrations.CreateModel(
            name='SystemTime',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.BigIntegerField()),
                ('time', models.DateTimeField()),
                ('system', models.CharField(max_length=255)),
            ],
            options={
                'unique_together': {('system', 'data')},
            },
        ),
    ]