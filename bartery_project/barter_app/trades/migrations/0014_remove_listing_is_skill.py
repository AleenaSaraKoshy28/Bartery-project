# Generated by Django 5.1.7 on 2025-03-27 15:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0013_alter_chatmessage_id_alter_listing_id_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='listing',
            name='is_skill',
        ),
    ]
