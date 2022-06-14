from django.db import models
from django.contrib.auth import get_user_model


class Song(models.Model):
    title = models.CharField(max_length=255)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    song_file = models.FileField(upload_to='songs/files/')
    duration = models.DurationField(blank=True, null=True)
    cover = models.ImageField(upload_to='songs/covers/', default='defaults/songs/default.png')
    created_at = models.DateTimeField(auto_now_add=True, editable=False)

    def delete(self, *args, **kwargs):
        self.song_file.delete()
        self.cover.delete()
        super().delete(*args, **kwargs)
