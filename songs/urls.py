from django.urls import path

from .views import SongViewSet

urlpatterns = [
    path('<uuid:public_id>/', SongViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'})),
    path('', SongViewSet.as_view({'post': 'create'})),
]
