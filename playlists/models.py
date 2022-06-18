from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import F

from songs.models import Song


class Playlist(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    cover = models.ImageField(upload_to='playlists/covers/', blank=True, default='defaults/playlists/default.png')
    description = models.TextField(max_length=500, blank=True, null=True)
    public = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'{self.title} ({self.pk})'


class PlaylistSong(models.Model):
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_songs', editable=False)
    song = models.ForeignKey(Song, on_delete=models.CASCADE, editable=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.playlist.title} - {self.song.title} - {self.order}'

    def delete(self, *args, **kwargs):
        playlist_songs = self.playlist.playlist_songs.all()
        playlist_songs_gte_order = playlist_songs.filter(order__gte=self.order)
        playlist_songs_gte_order.update(order=F('order') - 1)
        super().delete(*args, **kwargs)
