from rest_framework import serializers
from mutagen.mp3 import MP3
import datetime

from users.serializers import UserSerializer
from .models import Song
from .validators import HasExtension, IsAudio
from vibly.img import reshape_and_return_url, get_renamed_filename, delete_image


class CreateSongSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    song_file = serializers.FileField(validators=[HasExtension('mp3', 'ogg', 'wav'), IsAudio()])

    class Meta:
        model = Song
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'author', 'duration')

    def save(self, **kwargs):
        self.validated_data['song_file'].name = get_renamed_filename(self.validated_data['song_file'].name)
        self.validated_data['duration'] = \
            datetime.timedelta(seconds=float(MP3(self.validated_data['song_file']).info.length))

        self.validated_data['author'] = self.context['request'].user

        cover = self.validated_data.get('cover')
        self.validated_data.pop('cover', None)

        if cover:
            if self.instance:
                delete_image(self.instance.cover)

            self.validated_data['cover'] = reshape_and_return_url(cover,
                                                                  cover.name,
                                                                  self.Meta.model.cover.field.upload_to,
                                                                  height=512,
                                                                  width=512)

        return super().save(**kwargs)


class SongSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    song_file = serializers.SerializerMethodField()
    cover = serializers.SerializerMethodField()

    class Meta:
        model = Song
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'author', 'duration', 'song_file', 'public_id')

    def save(self, **kwargs):
        self.validated_data['author'] = self.context['request'].user

        cover = self.validated_data.get('cover')
        self.validated_data.pop('cover', None)

        song = super().save(**kwargs)

        if cover:
            if self.instance:
                delete_image(self.instance.pfp)

            self.validated_data['cover'] = reshape_and_return_url(cover,
                                                                  cover.name,
                                                                  self.Meta.model.cover.field.upload_to,
                                                                  height=512,
                                                                  width=512)

        return song

    def get_song_file(self, instance):
        if instance.public or instance.author == self.context['request'].user:
            return self.context['request'].build_absolute_uri(instance.song_file.url)
        return None

    def get_cover(self, instance):
        if not instance.album:
            return self.context['request'].build_absolute_uri(instance.cover.url)
        return self.context['request'].build_absolute_uri(instance.album.cover.url)
