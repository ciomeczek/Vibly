# Generated by Django 4.0.4 on 2022-06-15 12:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('albums', '0001_initial'),
        ('songs', '0002_alter_song_duration'),
    ]

    operations = [
        migrations.AddField(
            model_name='song',
            name='album',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='songs', to='albums.album'),
        ),
        migrations.AddField(
            model_name='song',
            name='public',
            field=models.BooleanField(default=True),
        ),
    ]