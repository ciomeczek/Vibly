import uuid

from django.db import models
from django.contrib.auth import get_user_model
from django.db.models import F

from songs.models import Song


class Album(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    title = models.CharField(max_length=255)
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    cover = models.ImageField(upload_to='albums/covers/', blank=True, default='defaults/albums/default.png')
    description = models.TextField(max_length=500, blank=True, null=True)
    public = models.BooleanField(default=False)
    created_at = models.DateField(auto_now_add=True, editable=False)

    def __str__(self):
        return f'{self.title} - ({self.id})'

    def delete(self, using=None, keep_parents=False):
        if self.cover.name != self.cover.field.default:
            self.cover.delete()
        return super().delete(using, keep_parents)


class AlbumPosition(models.Model):
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='album_positions', editable=False)
    order = models.IntegerField(default=0)
    song = models.OneToOneField(Song, on_delete=models.CASCADE, related_name='album_position', editable=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.album.title} - {self.song.title} - {self.order}'

    def delete(self, *args, **kwargs):
        album_positions = self.album.album_positions.all()
        album_positions_gte_order = album_positions.filter(order__gte=self.order)
        album_positions_gte_order.update(order=F('order') - 1)
        super().delete(*args, **kwargs)
