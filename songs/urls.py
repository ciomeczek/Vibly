from django.urls import path

from .views import SongViewSet

urlpatterns = [
    path('<song_pk>/', SongViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('', SongViewSet.as_view({'post': 'create'})),
]
