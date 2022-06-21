from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Playlist, PlaylistSong
from .serializers import PlaylistSerializer, \
    CreatePlaylistSerializer, \
    PlaylistSongSerializer, \
    CreatePlaylistSongSerializer


class PlaylistsViewSet(viewsets.ModelViewSet):
    lookup_field = 'public_id'
    queryset = Playlist.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        playlist = self.get_object()

        if playlist.author != request.user and not playlist.public:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(playlist)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        playlist = self.get_object()

        if playlist.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(playlist, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        playlist = self.get_object()

        if playlist.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(playlist)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePlaylistSerializer
        return PlaylistSerializer

    def get_permissions(self):
        if self.action == 'create' or self.action == 'partial_update':
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]


class PlaylistSongsViewSet(viewsets.ModelViewSet):
    multiple_lookup_fields = {'playlist': 'public_id', 'playlist_song': 'playlist_song_order'}
    playlist_queryset = Playlist.objects.all()
    playlist_song_queryset = PlaylistSong.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        playlist = self.get_playlist()

        if playlist.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data,
                                         context=self.get_serializer_context() | {'playlist': playlist})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        playlist = self.get_playlist()
        playlist_song = self.get_playlist_song()

        if playlist.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(playlist_song,
                                         data=request.data,
                                         partial=True,
                                         context=self.get_serializer_context() | {'playlist': playlist})

        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        playlist = self.get_playlist()
        playlist_song = self.get_playlist_song()

        if playlist.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(playlist_song)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreatePlaylistSongSerializer
        return PlaylistSongSerializer

    def get_playlist(self):
        playlist_pk_url = self.multiple_lookup_fields.get('playlist')
        playlist_pk = self.kwargs.get(playlist_pk_url)
        playlist = get_object_or_404(self.playlist_queryset, public_id=playlist_pk)
        self.check_object_permissions(self.request, playlist)
        return playlist

    def get_playlist_song(self):
        playlist_song_pk_url = self.multiple_lookup_fields.get('playlist_song')
        playlist_song_pk = self.kwargs.get(playlist_song_pk_url)
        playlist_song = get_object_or_404(self.playlist_song_queryset,
                                          order=playlist_song_pk,
                                          playlist=self.get_playlist())
        self.check_object_permissions(self.request, playlist_song)
        return playlist_song
