from django.urls import path

from .views import PlaylistsViewSet, PlaylistSongsViewSet

urlpatterns = [
    path('', PlaylistsViewSet.as_view({'post': 'create'})),
    path('<int:pk>/', PlaylistsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('<int:pk>/order/', PlaylistSongsViewSet.as_view({'post': 'create'})),
    path('<int:pk>/order/<int:playlist_song_order>/', PlaylistSongsViewSet.as_view({'patch': 'partial_update',
                                                                                    'delete': 'destroy'}))
]
