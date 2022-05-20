# Generated by Django 4.0.4 on 2022-05-12 18:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0002_alter_song_duration'),
        ('playlists', '0003_alter_playlist_songs'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='playlist',
            name='songs',
        ),
        migrations.CreateModel(
            name='PlaylistSong',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.IntegerField(default=0)),
                ('playlist', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='playlist_songs', to='playlists.playlist')),
                ('song', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='songs.song')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]