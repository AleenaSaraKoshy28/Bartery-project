# Generated by Django 5.1.7 on 2025-03-29 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0028_listing_offer_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='trade',
            name='rejected_skills',
            field=models.ManyToManyField(blank=True, related_name='rejected_by_profiles', to='trades.listing'),
        ),
    ]
