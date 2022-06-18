from django.urls import path

from .views import AlbumsViewSet, AlbumPositionsViewSet

urlpatterns = [
    path('', AlbumsViewSet.as_view({'post': 'create'})),
    path('<int:pk>/', AlbumsViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('<int:pk>/order/', AlbumPositionsViewSet.as_view({'post': 'create'})),
    path('<int:pk>/order/<int:album_position_order>/', AlbumPositionsViewSet.as_view({'patch': 'partial_update',
                                                                                      'delete': 'destroy'}))
]
