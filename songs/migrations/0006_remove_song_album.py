# Generated by Django 4.0.4 on 2022-06-17 18:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0005_alter_song_created_at'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='song',
            name='album',
        ),
    ]