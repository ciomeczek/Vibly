# Generated by Django 4.0.4 on 2022-06-15 12:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0004_alter_song_album'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='created_at',
            field=models.DateField(auto_now_add=True),
        ),
    ]
