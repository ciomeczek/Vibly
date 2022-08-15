import random

from rest_framework import status
from rest_framework.test import APITestCase

from songs.models import Song
from .models import Album, AlbumPosition
from songs.tests import SongCreate
from users.tests import UserCreate


class AlbumCreate:
    @staticmethod
    def create_album(user, **kwargs):
        data = {
            'title': 'test album',
            'author': user,
            'public': True
        }

        data.update(kwargs)

        return Album.objects.create(**data)

    @classmethod
    def create_album_position(cls, client, user, token, **kwargs):
        song = kwargs.pop('song', None) or SongCreate.create_song(client, token)
        album = kwargs.pop('album', None) or cls.create_album(user)

        order = random.randint(-3, album.album_positions.count())
        data = {
            'song_pk': song.public_id,
            'order': order
        }

        data.update(kwargs)

        response = client.post(f'/album/{album.public_id}/order/', data, HTTP_AUTHORIZATION='Bearer ' + token, format='json')

        return AlbumPosition.objects.filter(album=album, order=response.data.get('order')).first()


class AlbumTests(APITestCase):
    def setUp(self):
        user_dict = UserCreate.create_user_dict(self.client)
        self.user = user_dict.get('user')
        self.token = user_dict.get('token')

        def end():
            for album in Album.objects.all():
                album.delete()

            for song in Song.objects.all():
                song.delete()

        self.addCleanup(end)

    def create_album(self, **kwargs):
        return AlbumCreate.create_album(self.user, **kwargs)

    def create_album_position(self, **kwargs):
        return AlbumCreate.create_album_position(self.client, self.user, self.token, **kwargs)

    def create_song(self, **kwargs):
        return SongCreate.create_song(self.client, self.token, **kwargs)

    def test_create_album(self):
        cover = open('testfiles/armstrong.jpg', 'rb')

        data = {
            'title': 'test album',
            'public': True,
            'cover': cover
        }

        response = self.client.post('/album/', data, HTTP_AUTHORIZATION='Bearer ' + self.token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Album.objects.count(), 1)

        album = Album.objects.filter(public_id=response.data.get('public_id')).first()
        self.assertEqual(album.title, 'test album')
        self.assertEqual(album.author, self.user)
        self.assertTrue(album.public)
        self.assertEqual(album.cover.url, f'/{response.data.get("cover").split("/", 3)[-1]}')

    def test_create_album_position(self):
        songs = [self.create_song() for i in range(3)]

        data = {
            "title": "test album",
            "album_positions": [
                {
                    "song_pk": song.public_id,
                    "order": i
                } for i, song in zip([random.randint(-2, i + 3) for i in range(len(songs))], songs)
            ]
        }

        response = self.client.post('/album/', data, HTTP_AUTHORIZATION='Bearer ' + self.token, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        album = Album.objects.filter(public_id=response.data.get('public_id')).first()
        self.assertEqual(album.title, 'test album')
        self.assertEqual(album.author, self.user)
        self.assertFalse(album.public)

        album_positions = AlbumPosition.objects.filter(album=album)
        self.assertEqual(album_positions.count(), len(songs))

        for preferred_order, song in enumerate(songs, start=1):
            album_position = album_positions.filter(song=song).first()

            self.assertIsNotNone(album_position)
            self.assertEqual(album_position.order, preferred_order)

    def test_create_album_position_no_order(self):
        songs = [self.create_song() for i in range(3)]

        data = {
            "title": "test album",
            "album_positions": [
                {
                    "song_pk": song.public_id,
                } for song in songs
            ]
        }

        response = self.client.post('/album/', data, HTTP_AUTHORIZATION='Bearer ' + self.token, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        album = Album.objects.filter(public_id=response.data.get('public_id')).first()
        self.assertEqual(album.title, 'test album')
        self.assertEqual(album.author, self.user)
        self.assertFalse(album.public)

        album_positions = AlbumPosition.objects.filter(album=album)
        self.assertEqual(album_positions.count(), len(songs))

        for preferred_order, song in enumerate(songs, start=1):
            album_position = album_positions.filter(song=song).first()

            self.assertIsNotNone(album_position)
            self.assertEqual(album_position.order, preferred_order)

    def test_update_album(self):
        album = self.create_album()

        data = {
            'title': 'test album',
            'public': True
        }

        response = self.client.patch(f'/album/{album.public_id}/', data, HTTP_AUTHORIZATION='Bearer ' + self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        album = Album.objects.filter(pk=album.id).first()
        self.assertEqual(album.title, 'test album')
        self.assertEqual(album.author, self.user)
        self.assertTrue(album.public)

    def test_delete_album(self):
        album = self.create_album()

        for i in range(3):
            self.create_album_position(album=album)

        response = self.client.delete(f'/album/{album.public_id}/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Album.objects.count(), 0)
        self.assertEqual(AlbumPosition.objects.count(), 0)


class AlbumPositionTest(APITestCase):
    def setUp(self):
        user_dict = UserCreate.create_user_dict(self.client)
        self.user = user_dict.get('user')
        self.token = user_dict.get('token')

        def end():
            for album in Album.objects.all():
                album.delete()

            for song in Song.objects.all():
                song.delete()

        self.addCleanup(end)

    def create_album(self, **kwargs):
        return AlbumCreate.create_album(self.user, **kwargs)

    def create_album_position(self, **kwargs):
        return AlbumCreate.create_album_position(self.client, self.user, self.token, **kwargs)

    def create_song(self, **kwargs):
        return SongCreate.create_song(self.client, kwargs.get('user') or self.token, **kwargs)

    def create_user_dict(self, **kwargs):
        return UserCreate.create_user_dict(self.client, **kwargs)

    def test_create_album_position(self):
        album = self.create_album()
        songs = [self.create_song(title=f'Song number {i}') for i in range(0, 3)]

        orders = [20, -10, 10]
        sorted_order = [2, 1, 3]
        # the order with 10 will be the last because it is the biggest by the time it's in the database
        # requests are separate so by the second request orders will be [1, 2]
        # 10 is bigger than 2, so it will be the last

        for song, order in zip(songs, orders):
            data = {
                'song_pk': song.public_id,
                'order': order
            }

            response = self.client.post(f'/album/{album.public_id}/order/',
                                        data,
                                        HTTP_AUTHORIZATION=f'Bearer {self.token}')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        album_positions = AlbumPosition.objects.filter(album=album).order_by('order')
        self.assertEqual(album_positions.count(), len(songs))

        sorted_songs = [song for order, song in sorted(zip(sorted_order, songs))]
        for album_position, song in zip(album_positions, sorted_songs):
            self.assertEqual(album_position.song, song)

    def test_create_album_position_bad_song(self):
        album = self.create_album()

        token = self.create_user_dict().get('token')
        song = self.create_song(user=token)

        data = {
            'song_pk': song.public_id,
            'order': 10
        }
        response = self.client.post(f'/album/{album.public_id}/order/',
                                    data,
                                    HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(AlbumPosition.objects.count(), 0)

    def test_create_double_same_song(self):
        album = self.create_album()
        song = self.create_song()

        data = {
            'song_pk': song.public_id,
            'order': 10
        }

        response = self.client.post(f'/album/{album.public_id}/order/',
                                    data,
                                    HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(f'/album/{album.public_id}/order/',
                                    data,
                                    HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(AlbumPosition.objects.count(), 1)

    def test_update_album_position_to_left(self):
        album = self.create_album()

        for i in range(8):
            self.create_album_position(album=album)

        album_position = self.create_album_position(album=album, order=6)

        data = {
            'order': 3
        }

        response = self.client.patch(f'/album/{album.public_id}/order/{album_position.order}/',
                                     data,
                                     HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        album_positions = album.album_positions.all().order_by('order')

        for preferred_order, album_position in enumerate(album_positions, start=1):
            album_position = album_positions.filter(song=album_position.song).first()

            self.assertIsNotNone(album_position)
            self.assertEqual(album_position.order, preferred_order)

    def test_update_album_position_to_right(self):
        album = self.create_album()

        for i in range(8):
            self.create_album_position(album=album)

        album_position = self.create_album_position(album=album, order=3)

        data = {
            'order': 6
        }

        response = self.client.patch(f'/album/{album.public_id}/order/{album_position.order}/',
                                     data,
                                     HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        album_positions = album.album_positions.all().order_by('order')

        for preferred_order, album_position in enumerate(album_positions, start=1):
            album_position = album_positions.filter(song=album_position.song).first()

            self.assertIsNotNone(album_position)
            self.assertEqual(album_position.order, preferred_order)

    def test_update_song_pk(self):
        album = self.create_album()
        album_position = self.create_album_position(album=album)

        new_song = self.create_song()
        data = {
            'song_pk': new_song.public_id
        }

        response = self.client.patch(f'/album/{album.public_id}/order/{album_position.order}/',
                                     data,
                                     HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AlbumPosition.objects.filter(album=album).first().song.pk,
                         album_position.song.pk,
                         'Song has changed')

    def test_delete_album_position(self):
        album = self.create_album()

        for i in range(3):
            self.create_album_position(album=album)

        album_position = self.create_album_position(album=album, order=2)

        response = self.client.delete(f'/album/{album.public_id}/order/{album_position.order}/',
                                      HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AlbumPosition.objects.count(), 3)

        album_positions = album.album_positions.all()
        for preferred_order, album_position in enumerate(album_positions, start=1):
            album_position = album_positions.filter(song=album_position.song).first()

            self.assertIsNotNone(album_position)
            self.assertEqual(album_position.order, preferred_order)
