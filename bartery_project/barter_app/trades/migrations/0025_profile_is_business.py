# Generated by Django 5.1.7 on 2025-03-29 14:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0024_listing_estimated_value_listing_image_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='is_business',
            field=models.BooleanField(default=False),
        ),
    ]
