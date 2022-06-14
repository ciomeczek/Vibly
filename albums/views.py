from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Album, AlbumSong
from .serializers import AlbumSerializer, \
    CreateAlbumSerializer, \
    AlbumSongSerializer, \
    CreateAlbumSongSerializer


class AlbumsViewSet(viewsets.ModelViewSet):
    lookup_field = 'pk'
    queryset = Album.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        album = self.get_object()

        if album.author != request.user and not album.public:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(album)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        album = self.get_object()

        if album.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(album, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateAlbumSerializer
        return AlbumSerializer

    def get_permissions(self):
        if self.action == 'create' or self.action == 'partial_update':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class AlbumSongsViewSet(viewsets.ModelViewSet):
    multiple_lookup_fields = {'album': 'pk', 'album_song': 'album_song_order'}
    album_queryset = Album.objects.all()
    album_song_queryset = AlbumSong.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        album = self.get_album()
        request.data['album'] = album.pk

        if album.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        album = self.get_album()
        album_song = self.get_album_song()
        request.data['album'] = album.pk

        if album.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(album_song, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        album = self.get_album()
        album_song = self.get_album_song()

        if album.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(album_song)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateAlbumSongSerializer
        return AlbumSongSerializer

    def get_album(self):
        album_pk_url = self.multiple_lookup_fields.get('album')
        album_pk = self.kwargs.get(album_pk_url)
        album = get_object_or_404(self.album_queryset, pk=album_pk)
        self.check_object_permissions(self.request, album)
        return album

    def get_album_song(self):
        album_song_pk_url = self.multiple_lookup_fields.get('album_song')
        album_song_pk = self.kwargs.get(album_song_pk_url)
        album_song = get_object_or_404(self.album_song_queryset, order=album_song_pk)
        self.check_object_permissions(self.request, album_song)
        return album_song
