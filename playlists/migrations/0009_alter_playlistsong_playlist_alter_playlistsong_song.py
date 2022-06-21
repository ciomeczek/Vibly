# Generated by Django 4.0.4 on 2022-06-19 20:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0006_remove_song_album'),
        ('playlists', '0008_rename_name_playlist_title'),
    ]

    operations = [
        migrations.AlterField(
            model_name='playlistsong',
            name='playlist',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='playlist_songs', to='playlists.playlist'),
        ),
        migrations.AlterField(
            model_name='playlistsong',
            name='song',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, to='songs.song'),
        ),
    ]