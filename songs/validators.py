from rest_framework import serializers
from mutagen.mp3 import MP3, HeaderNotFoundError


class HasExtension:
    def __init__(self, *args):
        self.extensions = args

    def __call__(self, file):
        for ext in self.extensions:
            if ext == file.name.split('.')[-1]:
                return True

        raise serializers.ValidationError(
            f'File extension not allowed. Allowed extensions: {", ".join(self.extensions)}'
        )


class IsAudio:
    def __call__(self, file):
        try:
            MP3(file)
        except HeaderNotFoundError:
            raise serializers.ValidationError('File is not an audio file')

