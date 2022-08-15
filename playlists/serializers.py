from rest_framework import serializers
from django.db.models import F, Max

from .models import Playlist, PlaylistSong
from users.serializers import UserSerializer
from songs.models import Song
from songs.serializers import SongSerializer
from vibly.img import reshape_and_return_url, delete_image


class PlaylistSongSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    song_pk = serializers.SlugRelatedField(
        source='song', read_only=True, slug_field='public_id'
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

        playlist_songs = playlist.playlist_songs.all()
        max_order = (playlist_songs.aggregate(Max('order'))['order__max'] or 0) + 1

        if order is None:
            order = self.instance.order if self.instance is not None else max_order
        else:
            # clamp between 1 and max_order
            order = max(min(order, max_order), 1)

        self.validated_data['order'] = order
        self.validated_data['playlist'] = playlist

        return super().save(**kwargs)

    def create(self, validated_data):
        order = validated_data.get('order')
        playlist = validated_data.get('playlist')

        playlist_songs = playlist.playlist_songs.all()

        if PlaylistSong.objects.filter(playlist=playlist, order=order).exists():
            songs_gte_order = playlist_songs.filter(order__gte=order)
            songs_gte_order.update(order=F('order') + 1)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        order = validated_data.get('order')
        playlist = validated_data.get('playlist')

        playlist_songs = playlist.playlist_songs.all()

        if PlaylistSong.objects.filter(playlist=playlist, order=order).exists():
            if instance.order < order:
                songs_query = playlist_songs.filter(order__lte=order, order__gt=instance.order)
                songs_query.update(order=F('order') - 1)
            elif instance.order > order:
                songs_query = playlist_songs.filter(order__gte=order, order__lt=instance.order)
                songs_query.update(order=F('order') + 1)

        return super().update(instance, validated_data)


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
            new_data = {'song_pk': data.get('song').public_id}

            serializer = self.child.__class__(data=new_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save(**kwargs)
            result.append(serializer.instance)

        return result


class CreatePlaylistSongSerializer(PlaylistSongSerializer):
    song_pk = serializers.SlugRelatedField(
        queryset=Song.objects.all(), source='song', write_only=True, slug_field='public_id'
    )

    class Meta(PlaylistSongSerializer.Meta):
        list_serializer_class = CreatePlaylistSongListSerializer
        fields = ['song', 'song_pk', 'order']


class PlaylistSerializer(serializers.ModelSerializer):
    playlist_songs = PlaylistSongSerializer(many=True, required=False, read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = Playlist
        fields = ['public_id', 'title', 'author', 'playlist_songs', 'cover', 'description', 'public', 'created_at']

    def save(self, **kwargs):
        self.validated_data['author'] = self.context.get('request').user

        cover = self.validated_data.pop('cover', None)

        if cover:
            if self.instance:
                delete_image(self.instance.cover)

            self.validated_data['cover'] = reshape_and_return_url(cover,
                                                                  cover.name,
                                                                  self.Meta.model.cover.field.upload_to,
                                                                  height=512,
                                                                  width=512)

        self.instance = self.instance or Playlist.objects.create(**self.validated_data)
        return self.instance


class CreatePlaylistSerializer(PlaylistSerializer):
    playlist_songs = CreatePlaylistSongSerializer(many=True, required=False)

    def save(self, **kwargs):
        playlist_songs = self.validated_data.pop('playlist_songs', None)
        super().save(**kwargs)

        self.context['playlist'] = self.instance
        if playlist_songs is not None:
            for playlist_song in playlist_songs:
                playlist_song['song_pk'] = playlist_song.pop('song').public_id

            serializer = CreatePlaylistSongSerializer(data=playlist_songs, context=self.context, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return self.instance
