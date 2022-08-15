from rest_framework import serializers
from django.db.models import F, Max

from .models import Album, AlbumPosition
from users.serializers import UserSerializer
from songs.models import Song
from songs.serializers import SongSerializer
from vibly.img import reshape_and_return_url, delete_image


class AlbumPositionSerializer(serializers.ModelSerializer):
    song = SongSerializer(read_only=True)
    song_pk = serializers.SlugRelatedField(
        source='song', read_only=True, slug_field='public_id'
    )

    order = serializers.IntegerField(required=False)

    class Meta:
        model = AlbumPosition
        fields = ['song', 'order', 'song_pk']
        read_only_fields = ['song', 'song_pk']

    def validate(self, attrs):
        if self.instance is not None:
            return attrs

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

        album_positions = album.album_positions.all()
        max_order = (album_positions.aggregate(Max('order'))['order__max'] or 0) + 1

        if order is None:
            order = self.instance.order if self.instance is not None else max_order
        else:
            # clamp between 1 and max_order
            order = max(min(order, max_order), 1)

        self.validated_data['order'] = order
        self.validated_data['album'] = album

        return super().save(**kwargs)

    def create(self, validated_data):
        order = validated_data.get('order')
        album = validated_data.get('album')

        album_positions = album.album_positions.all()

        if AlbumPosition.objects.filter(album=album, order=order).exists():
            songs_gte_order = album_positions.filter(order__gte=order)
            songs_gte_order.update(order=F('order') + 1)

        return super().create(validated_data)

    def update(self, instance, validated_data):
        order = validated_data.get('order')
        album = validated_data.get('album')

        album_positions = album.album_positions.all()

        if AlbumPosition.objects.filter(album=album, order=order).exists():
            if instance.order < order:
                songs_query = album_positions.filter(order__lte=order, order__gt=instance.order)
                songs_query.update(order=F('order') - 1)
            elif instance.order > order:
                songs_query = album_positions.filter(order__gte=order, order__lt=instance.order)
                songs_query.update(order=F('order') + 1)

        return super().update(instance, validated_data)


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
            new_data = {'song_pk': data.get('song').public_id}

            serializer = self.child.__class__(data=new_data, context=self.context)
            serializer.is_valid(raise_exception=True)
            serializer.save(**kwargs)
            result.append(serializer.instance)

        return result


class CreateAlbumPositionSerializer(AlbumPositionSerializer):
    song_pk = serializers.SlugRelatedField(
        queryset=Song.objects.all(), source='song', write_only=True, slug_field='public_id'
    )

    class Meta(AlbumPositionSerializer.Meta):
        list_serializer_class = CreateAlbumPositionListSerializer
        fields = ['song', 'order', 'song_pk']


class AlbumSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    album_positions = AlbumPositionSerializer(many=True, required=False)

    class Meta:
        model = Album
        fields = ['title', 'author', 'description', 'cover', 'album_positions', 'created_at', 'public', 'public_id']
        read_only_fields = ['author']

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

        self.instance = self.instance or Album.objects.create(**self.validated_data)
        return self.instance


class CreateAlbumSerializer(AlbumSerializer):
    album_positions = CreateAlbumPositionSerializer(many=True, required=False)

    def save(self, **kwargs):
        album_positions = self.validated_data.pop('album_positions', None)
        super().save(**kwargs)

        self.context['album'] = self.instance
        if album_positions is not None:
            for album_position in album_positions:
                album_position['song_pk'] = album_position.pop('song').public_id

            serializer = CreateAlbumPositionSerializer(data=album_positions, context=self.context, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

        return self.instance
