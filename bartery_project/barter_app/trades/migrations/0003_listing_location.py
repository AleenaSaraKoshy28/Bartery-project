# Generated by Django 5.1.4 on 2024-12-16 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0002_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='location',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
