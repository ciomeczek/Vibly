from rest_framework import serializers
from django.db.models import F, Max

from .models import Album, AlbumPosition
from users.serializers import UserSerializer
from songs.models import Song
from songs.serializers import SongSerializer
from vibly.img import reshape_and_return_url, delete_image


class AlbumPositionSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    song_pk = serializers.PrimaryKeyRelatedField(
        queryset=Song.objects.all(), source='song', write_only=True
    )

    order = serializers.IntegerField(required=False)

    class Meta:
        model = AlbumPosition
        fields = ['song', 'order', 'song_pk']

    def validate(self, attrs):
        if attrs.get('song').author != self.context.get('request').user:
            raise serializers.ValidationError({'song_pk': 'You can only add your songs to your album'})

        return attrs

    def validate_song_pk(self, song):
        if song.album is not None:
            raise serializers.ValidationError(f'{song.title} already belongs to an album')
        return song

    def save(self, **kwargs):
        order = self.validated_data.get('order')

        album = self.context.get('album')
        self.validated_data['album'] = album

        if album is None:
            raise Exception('You must include album in context')

        if order is None:
            order = album.album_positions.count() + 1

        album_positions = album.album_positions.all()

        max_order = album_positions.aggregate(Max('order'))['order__max'] or 0
        if order > max_order:
            self.validated_data['order'] = max_order + 1

        if AlbumPosition.objects.filter(album=album, order=order).exists():
            songs_gte_order = album_positions.filter(order__gte=order)
            songs_gte_order.update(order=F('order') + 1)

        return super().save(**kwargs)


class CreateAlbumPositionListSerializer(serializers.ListSerializer):
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
            new_data = {'song_pk': data.get('song').pk}

            serializer = self.child.__class__(data=new_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save(**kwargs)
            result.append(serializer.instance)

        return result


class CreateAlbumPositionSerializer(AlbumPositionSerializer):
    class Meta(AlbumPositionSerializer.Meta):
        list_serializer_class = CreateAlbumPositionListSerializer
        fields = ['song', 'order', 'song_pk']
        extra_kwargs = {
            'song_pk': {'write_only': True}
        }


class AlbumSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    album_positions = AlbumPositionSerializer(many=True, required=False)

    class Meta:
        model = Album
        fields = '__all__'

    def save(self, **kwargs):
        album_positions = self.validated_data.pop('album_positions', None)
        self.validated_data['author'] = self.context.get('request').user

        cover = self.validated_data.pop('cover', None)

        self.instance = self.instance or Album.objects.create(**self.validated_data)

        if cover:
            if self.instance:
                delete_image(self.instance.pfp)

            self.validated_data['cover'] = reshape_and_return_url(cover,
                                                                  cover.name,
                                                                  self.Meta.model.cover.field.upload_to,
                                                                  height=128,
                                                                  width=128)

        if album_positions is not None:
            for album_position in album_positions:
                album_position['album_pk'] = self.instance.pk
                album_position['song_pk'] = album_position.pop('song').pk

            serializer = CreateAlbumPositionSerializer(data=album_positions,
                                                       context=self.context | {'album': self.instance},
                                                       many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return self.instance
