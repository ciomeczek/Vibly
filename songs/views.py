from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import SongSerializer, CreateSongSerializer
from .models import Song


class SongViewSet(viewsets.ModelViewSet):
    lookup_url_kwarg = 'song_pk'
    queryset = Song.objects.all()
    serializer_class = SongSerializer

    def create(self, request, *args, **kwargs):
        request.data['author'] = request.user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        song = self.get_object()
        serializer = self.get_serializer(song)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        song = self.get_object()

        if song.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(song, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        song = self.get_object()

        if song.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(song)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'retrieve':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateSongSerializer
        return SongSerializer
