from rest_framework import serializers
from django.db.models import F, Max

from .models import Playlist, PlaylistSong
from users.serializers import UserSerializer
from songs.models import Song
from songs.serializers import SongSerializer
from vibly.img import reshape_and_save


class PlaylistSongSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    song_pk = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(), source='song', write_only=True
    )

    order = serializers.IntegerField(required=False)

    class Meta:
        model = PlaylistSong
        fields = ['song', 'order', 'song_pk']

    def is_valid(self, raise_exception=False):
        playlist = Playlist.objects.get(pk=self.initial_data['playlist'])

        if self.initial_data.get('order') is None:
            self.initial_data['order'] = playlist.playlist_songs.count() + 1

        return super().is_valid(raise_exception)

    def save(self, **kwargs):
        order = self.validated_data.get('order')

        if order is None:
            playlist = self.validated_data.get('playlist')
            self.validated_data['order'] = playlist.playlist_songs.count() + 1

        playlist = self.validated_data.get('playlist') or self.instance.playlist
        playlist_songs = playlist.playlist_songs.all()

        max_order = playlist_songs.aggregate(Max('order'))['order__max'] or 0
        if order > max_order:
            self.validated_data['order'] = max_order + 1

        if PlaylistSong.objects.filter(playlist=playlist, order=order).exists():
            songs_gte_order = playlist_songs.filter(order__gte=order)
            songs_gte_order.update(order=F('order') + 1)

        return super().save(**kwargs)


class CreatePlaylistSongSerializer(PlaylistSongSerializer):
    class Meta(PlaylistSongSerializer.Meta):
        fields = ['playlist', 'song', 'order', 'song_pk']
        extra_kwargs = {
            'playlist': {'write_only': True},
            'song_pk': {'write_only': True}
        }


class CreatePlaylistSerializer(serializers.ModelSerializer):
    playlist_songs = PlaylistSongSerializer(many=True, read_only=False, required=False)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = '__all__'
        read_only_fields = ['author']

    def create(self, validated_data):
        playlist_songs = validated_data.pop('playlist_songs', None)
        validated_data['author'] = self.context.get('request').user

        cover = validated_data.pop('cover', None)

        playlist = Playlist.objects.create(**validated_data)

        if cover:
            reshape_and_save(cover, cover.name, playlist.cover, height=512, width=512, delete_old=True)

        if playlist_songs is not None:
            for playlist_song in playlist_songs:
                playlist_song['playlist'] = playlist.pk
                playlist_song['song_pk'] = playlist_song.pop('song').pk

                serializer = CreatePlaylistSongSerializer(data=playlist_song, context=self.context)
                serializer.is_valid(raise_exception=True)
                serializer.save()

        return playlist


class PlaylistSerializer(serializers.ModelSerializer):
    playlist_songs = PlaylistSongSerializer(many=True, read_only=False)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = '__all__'
        read_only_fields = ['author']
