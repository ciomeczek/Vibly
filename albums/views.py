from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from .models import Album, AlbumPosition
from .serializers import AlbumSerializer, \
    CreateAlbumSerializer, \
    AlbumPositionSerializer, \
    CreateAlbumPositionSerializer


class AlbumsViewSet(viewsets.ModelViewSet):
    lookup_field = 'public_id'
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

        serializer = self.get_serializer(album,
                                         data=request.data,
                                         partial=True,
                                         context=self.get_serializer_context() | {'album': album})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        album = self.get_object()

        if album.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(album)
        return Response(status=status.HTTP_204_NO_CONTENT)

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


class AlbumPositionsViewSet(viewsets.ModelViewSet):
    multiple_lookup_fields = {'album': 'public_id', 'album_position': 'album_position_order'}
    album_queryset = Album.objects.all()
    album_position_queryset = AlbumPosition.objects.all()
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        album = self.get_album()

        if album.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data, context=self.get_serializer_context() | {'album': album})
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        album = self.get_album()
        album_position = self.get_album_position()

        if album.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(album_position,
                                         data=request.data,
                                         partial=True,
                                         context=self.get_serializer_context() | {'album': album})
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        album = self.get_album()
        album_position = self.get_album_position()

        if album.author != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        self.perform_destroy(album_position)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateAlbumPositionSerializer
        return AlbumPositionSerializer

    def get_album(self):
        album_pk_url = self.multiple_lookup_fields.get('album')
        album_pk = self.kwargs.get(album_pk_url)
        album = get_object_or_404(self.album_queryset, public_id=album_pk)
        self.check_object_permissions(self.request, album)
        return album

    def get_album_position(self):
        album_position_pk_url = self.multiple_lookup_fields.get('album_position')
        album_position_pk = self.kwargs.get(album_position_pk_url)
        album_position = get_object_or_404(self.album_position_queryset,
                                           order=album_position_pk,
                                           album=self.get_album())
        self.check_object_permissions(self.request, album_position)
        return album_position
