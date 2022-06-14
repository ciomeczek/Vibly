from django.contrib import admin

from .models import Album, AlbumSong


admin.site.register(Album)
admin.site.register(AlbumSong)
