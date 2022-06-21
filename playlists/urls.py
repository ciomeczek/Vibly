from django.urls import path

from .views import PlaylistsViewSet, PlaylistSongsViewSet

urlpatterns = [
    path('', PlaylistsViewSet.as_view({'post': 'create'})),
    path('<uuid:public_id>/',
         PlaylistsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('<uuid:public_id>/order/', PlaylistSongsViewSet.as_view({'post': 'create'})),
    path('<uuid:public_id>/order/<int:playlist_song_order>/', PlaylistSongsViewSet.as_view({'patch': 'partial_update',
                                                                                            'delete': 'destroy'}))
]
