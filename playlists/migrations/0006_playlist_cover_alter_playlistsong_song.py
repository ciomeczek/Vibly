# Generated by Django 4.0.4 on 2022-05-12 19:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0002_alter_song_duration'),
        ('playlists', '0005_alter_playlistsong_song'),
    ]

    operations = [
        migrations.AddField(
            model_name='playlist',
            name='cover',
            field=models.ImageField(blank=True, default='defaults/playlists/default.png', upload_to='playlists/covers/'),
        ),
        migrations.AlterField(
            model_name='playlistsong',
            name='song',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='songs.song'),
        ),
    ]