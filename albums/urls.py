from django.urls import path

from .views import AlbumsViewSet, AlbumSongsViewSet

urlpatterns = [
    path('', AlbumsViewSet.as_view({'post': 'create'})),
    path('<int:pk>/', AlbumsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update'})),
    path('<int:pk>/order/', AlbumSongsViewSet.as_view({'post': 'create'})),
    path('<int:pk>/order/<int:album_song_order>/', AlbumSongsViewSet.as_view({'patch': 'partial_update',
                                                                              'delete': 'destroy'}))
]
