from rest_framework import serializers
from django.db.models import F, Max

from .models import Playlist, PlaylistSong
from users.serializers import UserSerializer
from songs.models import Song
from songs.serializers import SongSerializer
from vibly.img import reshape_and_return_url, delete_image


class PlaylistSongSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    song_pk = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(), source='song', write_only=True
    )

    order = serializers.IntegerField(required=False)

    class Meta:
        model = PlaylistSong
        fields = ['song', 'order', 'song_pk']

    def validate_song_pk(self, song_pk):
        if not song_pk.public:
            raise serializers.ValidationError(f'Can\'t add {song_pk.title}')
        return song_pk

    def save(self, **kwargs):
        order = self.validated_data.get('order')

        playlist = self.context.get('playlist')
        self.validated_data['playlist'] = playlist

        if playlist is None:
            raise Exception('You must include playlist in context')

        if order is None:
            order = playlist.playlist_songs.count() + 1

        playlist_songs = playlist.playlist_songs.all()

        max_order = playlist_songs.aggregate(Max('order'))['order__max'] or 0
        if order > max_order:
            self.validated_data['order'] = max_order + 1

        if PlaylistSong.objects.filter(playlist=playlist, order=order).exists():
            songs_gte_order = playlist_songs.filter(order__gte=order)
            songs_gte_order.update(order=F('order') + 1)

        return super().save(**kwargs)


class CreatePlaylistSongListSerializer(serializers.ListSerializer):
    def is_valid(self, raise_exception=False):
        errors = []
        for data in self.initial_data:
            serializer = self.child.__class__(data=data, context=self.context)
            serializer.is_valid(raise_exception=False)
            if serializer.errors:
                errors.append(serializer.errors)

        if errors:
            raise serializers.ValidationError(errors)

        return super().is_valid(raise_exception)

    def save(self, **kwargs):
        result = []
        for data in self.validated_data:
            new_data = {'song_pk': data.get('song').pk, 'playlist_pk': data.get('playlist').pk}

            serializer = self.child.__class__(data=new_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save(**kwargs)
            result.append(serializer.instance)

        return result


class CreatePlaylistSongSerializer(PlaylistSongSerializer):
    class Meta(PlaylistSongSerializer.Meta):
        list_serializer_class = CreatePlaylistSongListSerializer
        fields = ['song', 'song_pk', 'order']
        extra_kwargs = {
            'song_pk': {'write_only': True}
        }


class PlaylistSerializer(serializers.ModelSerializer):
    playlist_songs = PlaylistSongSerializer(many=True, read_only=False, required=False)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = '__all__'
        read_only_fields = ['author']

    def save(self, **kwargs):
        playlist_songs = self.validated_data.pop('playlist_songs', None)
        self.validated_data['author'] = self.context.get('request').user

        cover = self.validated_data.pop('cover', None)

        self.instance = Playlist.objects.create(**self.validated_data)

        if cover:
            if self.instance:
                delete_image(self.instance.pfp)

            self.instance.cover = reshape_and_return_url(cover,
                                                         cover.name,
                                                         self.Meta.model.cover.field.upload_to,
                                                         height=128,
                                                         width=128)
            self.save()

        self.context['playlist'] = self.instance
        if playlist_songs is not None:
            for playlist_song in playlist_songs:
                playlist_song['song_pk'] = playlist_song.pop('song').pk

            serializer = CreatePlaylistSongSerializer(data=playlist_songs, context=self.context, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return self.instance
