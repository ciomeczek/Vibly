from rest_framework import serializers
from django.db.models import F, Max

from .models import Album, AlbumSong
from users.serializers import UserSerializer
from songs.models import Song
from songs.serializers import SongSerializer
from vibly.img import reshape_and_save


class AlbumSongSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    song_pk = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(), source='song', write_only=True
    )

    order = serializers.IntegerField(required=False)

    class Meta:
        model = AlbumSong
        fields = ['song', 'order', 'song_pk']

    def is_valid(self, raise_exception=False):
        album = Album.objects.get(pk=self.initial_data['album'])

        if self.initial_data.get('order') is None:
            self.initial_data['order'] = album.album_songs.count() + 1

        if self.initial_data.get('song_pk'):
            song = Song.objects.get(pk=self.initial_data.get('song_pk'))
            if song.author != album.author:
                raise serializers.ValidationError({'song_pk': 'Song author does not match album author'})

        return super().is_valid(raise_exception)

    def save(self, **kwargs):
        order = self.validated_data.get('order')

        if order is None:
            album = self.validated_data.get('album')
            self.validated_data['order'] = album.album_songs.count() + 1

        album = self.validated_data.get('album') or self.instance.album
        album_songs = album.album_songs.all()

        max_order = album_songs.aggregate(Max('order'))['order__max'] or 0
        if order > max_order:
            self.validated_data['order'] = max_order + 1

        if AlbumSong.objects.filter(album=album, order=order).exists():
            songs_gte_order = album_songs.filter(order__gte=order)
            songs_gte_order.update(order=F('order') + 1)

        return super().save(**kwargs)


class CreateAlbumSongSerializer(AlbumSongSerializer):
    class Meta(AlbumSongSerializer.Meta):
        fields = ['album', 'song', 'order', 'song_pk']
        extra_kwargs = {
            'album': {'write_only': True},
            'song_pk': {'write_only': True}
        }


class CreateAlbumSerializer(serializers.ModelSerializer):
    album_songs = AlbumSongSerializer(many=True, read_only=False, required=False)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Album
        fields = '__all__'
        read_only_fields = ['author']

    def create(self, validated_data):
        album_songs = validated_data.pop('album_songs', None)
        validated_data['author'] = self.context.get('request').user

        cover = validated_data.pop('cover', None)

        album = Album.objects.create(**validated_data)

        if cover:
            reshape_and_save(cover, cover.name, album.cover, height=512, width=512, delete_old=True)

        if album_songs is not None:
            for album_song in album_songs:
                album_song['album'] = album.pk
                album_song['song_pk'] = album_song.pop('song').pk

                serializer = CreateAlbumSongSerializer(data=album_song, context=self.context)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        return album


class AlbumSerializer(serializers.ModelSerializer):
    album_songs = AlbumSongSerializer(many=True, read_only=False)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Album
        fields = '__all__'
        read_only_fields = ['author']
