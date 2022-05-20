from rest_framework import serializers
from mutagen.mp3 import MP3
import datetime

from users.serializers import UserSerializer
from .models import Song
from .validators import HasExtension, IsAudio
from vibly.img import reshape_and_save, get_renamed_filename
from albums.serializers import AlbumSerializer


class CreateSongSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    song_file = serializers.FileField(validators=[HasExtension('mp3', 'ogg', 'wav'), IsAudio()])

    class Meta:
        model = Song
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'author', 'duration')

    def save(self, **kwargs):
        self.validated_data['song_file'].name = get_renamed_filename(self.validated_data['song_file'].name)
        self.validated_data['duration'] =\
            datetime.timedelta(seconds=float(MP3(self.validated_data['song_file']).info.length))

        self.validated_data['author'] = self.context['request'].user

        cover = self.validated_data.get('cover')
        self.validated_data.pop('cover', None)

        song = super().save(**kwargs)

        if cover:
            reshape_and_save(cover, cover.name, song.cover, height=512, width=512, delete_old=True)

        return song


class SongSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    AlbumSerializer = AlbumSerializer(read_only=True)

    class Meta:
        model = Song
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'author', 'duration', 'song_file')

    def save(self, **kwargs):
        cover = self.validated_data.get('cover')
        self.validated_data.pop('cover', None)

        song = super().save(**kwargs)

        if cover:
            reshape_and_save(cover, cover.name, song.cover, height=512, width=512, delete_old=True)

        return song
