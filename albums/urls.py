from django.urls import path

from .views import AlbumsViewSet, AlbumPositionsViewSet

urlpatterns = [
    path('', AlbumsViewSet.as_view({'post': 'create'})),
    path('<uuid:public_id>/',
         AlbumsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('<uuid:public_id>/order/', AlbumPositionsViewSet.as_view({'post': 'create'})),
    path('<uuid:public_id>/order/<int:album_position_order>/',
         AlbumPositionsViewSet.as_view({'patch': 'partial_update',
                                        'delete': 'destroy'}))
]
