# Generated by Django 4.0.4 on 2022-06-17 21:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('songs', '0006_remove_song_album'),
        ('albums', '0002_albumposition_delete_albumsong'),
    ]

    operations = [
        migrations.AlterField(
            model_name='albumposition',
            name='album',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='album_songs', to='albums.album'),
        ),
        migrations.AlterField(
            model_name='albumposition',
            name='song',
            field=models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, related_name='album_position', to='songs.song'),
        ),
    ]