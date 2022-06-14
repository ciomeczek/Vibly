from django.db import models
from django.contrib.auth import get_user_model

from songs.models import Song


class Album(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    cover = models.ImageField(upload_to='albums/covers/', blank=True, default='defaults/albums/default.png')
    description = models.TextField(max_length=500, blank=True, null=True)
    public = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True, editable=False)

    def __str__(self):
        return self.title


class AlbumSong(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='album_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.album.name} - {self.song.title} - {self.order}'
