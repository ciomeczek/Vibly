from django.db import models
from django.contrib.auth import get_user_model


class Song(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    song_file = models.FileField(upload_to='songs/files/')
    duration = models.DurationField(blank=True, null=True)
    cover = models.ImageField(upload_to='songs/covers/', default='defaults/songs/default.png')
    public = models.BooleanField(default=True)
    created_at = models.DateField(auto_now_add=True, editable=False)

    @property
    def album(self):
        if hasattr(self, 'album_position'):
            return self.album_position.album
        return None

    def delete(self, *args, **kwargs):
        self.song_file.delete()
        self.cover.delete()
        super().delete(*args, **kwargs)
