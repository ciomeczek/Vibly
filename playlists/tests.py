import json
import random
from pprint import pprint

from rest_framework import status
from rest_framework.test import APITestCase

from songs.models import Song
from users.tests import UserCreate
from .models import Playlist, PlaylistSong

from songs.tests import SongCreate


class PlaylistCreate:
    @staticmethod
    def create_playlist(user, **kwargs):
        data = {
            'title': 'test playlist',
            'author': user,
            'public': True
        }

        data.update(kwargs)

        return Playlist.objects.create(**data)

    @classmethod
    def create_playlist_song(cls, client, user, token, **kwargs):
        song = kwargs.get('song') or SongCreate.create_song(client, token)
        playlist = kwargs.get('playlist') or cls.create_playlist(user)

        order = random.randint(-3, playlist.playlist_songs.count())
        data = {
            'song_pk': song.public_id,
            'order': order
        }

        data.update(kwargs)

        response = client.post(f'/playlist/{playlist.public_id}/order/', data, HTTP_AUTHORIZATION='Bearer ' + token)

        return PlaylistSong.objects.filter(playlist=playlist, order=response.data.get('order')).first()


class PlaylistTests(APITestCase):
    def setUp(self):
        user_dict = UserCreate.create_user_dict(self.client)
        self.user = user_dict.get('user')
        self.token = user_dict.get('token')

        def end():
            for playlist in Playlist.objects.all():
                playlist.delete()

            for song in Song.objects.all():
                song.delete()

        self.addCleanup(end)

    def create_playlist(self, **kwargs):
        return PlaylistCreate.create_playlist(self.user, **kwargs)

    def create_playlist_song(self, **kwargs):
        return PlaylistCreate.create_playlist_song(self.client, self.user, self.token, **kwargs)

    def create_song(self, **kwargs):
        return SongCreate.create_song(self.client, self.token, **kwargs)

    def test_create_playlist(self):
        cover = open('testfiles/armstrong.jpg', 'rb')

        data = {
            'title': 'test playlist',
            'public': True,
            'cover': cover
        }

        response = self.client.post('/playlist/', data, HTTP_AUTHORIZATION='Bearer ' + self.token)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Playlist.objects.count(), 1)

        playlist = Playlist.objects.filter(pk=response.data.get('id')).first()
        self.assertEqual(playlist.title, 'test playlist')
        self.assertEqual(playlist.author, self.user)
        self.assertTrue(playlist.public)
        self.assertEqual(playlist.cover.url, f'/{response.data.get("cover").split("/", 3)[-1]}')

    def test_create_playlist_song(self):
        songs = [self.create_song() for i in range(3)]

        data = {
            "title": "test playlist",
            "playlist_songs": [
                {
                    "song_pk": str(song.public_id),
                    "order": i
                } for i, song in zip([random.randint(-100, 100) for i in range(len(songs))], songs)
            ]
        }

        response = self.client.post('/playlist/', data, HTTP_AUTHORIZATION='Bearer ' + self.token, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        playlist = Playlist.objects.filter(pk=response.data.get('id')).first()
        self.assertEqual(playlist.title, 'test playlist')
        self.assertEqual(playlist.author, self.user)
        self.assertFalse(playlist.public)

        playlist_songs = PlaylistSong.objects.filter(playlist=playlist)
        self.assertEqual(playlist_songs.count(), len(songs))

        for preferred_order, song in enumerate(songs, start=1):
            playlist_song = playlist_songs.filter(song=song).first()

            self.assertIsNotNone(playlist_song)
            self.assertEqual(playlist_song.order, preferred_order)

    def test_create_playlist_song_no_order(self):
        songs = [self.create_song() for i in range(3)]

        data = {
            "title": "test playlist",
            "playlist_songs": [
                {
                    "song_pk": song.public_id
                } for song in songs
            ]
        }

        response = self.client.post('/playlist/', data, HTTP_AUTHORIZATION='Bearer ' + self.token, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        playlist = Playlist.objects.filter(pk=response.data.get('id')).first()
        self.assertEqual(playlist.title, 'test playlist')
        self.assertEqual(playlist.author, self.user)
        self.assertFalse(playlist.public)

        playlist_songs = PlaylistSong.objects.filter(playlist=playlist)
        self.assertEqual(playlist_songs.count(), len(songs))

        for preferred_order, song in enumerate(songs, start=1):
            playlist_song = playlist_songs.filter(song=song).first()

            self.assertIsNotNone(playlist_song)
            self.assertEqual(playlist_song.order, preferred_order)

    def test_update_playlist(self):
        playlist = self.create_playlist()

        data = {
            'title': 'test playlist',
            'public': True
        }

        response = self.client.patch(f'/playlist/{playlist.public_id}/', data, HTTP_AUTHORIZATION='Bearer ' + self.token)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        playlist = Playlist.objects.filter(pk=playlist.id).first()
        self.assertEqual(playlist.title, 'test playlist')
        self.assertEqual(playlist.author, self.user)
        self.assertTrue(playlist.public)

    def test_delete_playlist(self):
        playlist = self.create_playlist()

        for i in range(3):
            self.create_playlist_song(playlist=playlist)

        response = self.client.delete(f'/playlist/{playlist.public_id}/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Playlist.objects.count(), 0)
        self.assertEqual(PlaylistSong.objects.count(), 0)


class PlaylistSongTest(APITestCase):
    def setUp(self):
        user_dict = UserCreate.create_user_dict(self.client)
        self.user = user_dict.get('user')
        self.token = user_dict.get('token')

        def end():
            for playlist in Playlist.objects.all():
                playlist.delete()

            for song in Song.objects.all():
                song.delete()

        self.addCleanup(end)

    def create_playlist(self, **kwargs):
        return PlaylistCreate.create_playlist(self.user, **kwargs)

    def create_playlist_song(self, **kwargs):
        return PlaylistCreate.create_playlist_song(self.client, self.user, self.token, **kwargs)

    def create_song(self, **kwargs):
        return SongCreate.create_song(self.client, self.token, **kwargs)

    def test_create_playlist_song(self):
        playlist = self.create_playlist()
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

            response = self.client.post(f'/playlist/{playlist.public_id}/order/',
                                        data,
                                        HTTP_AUTHORIZATION=f'Bearer {self.token}')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        playlist_songs = PlaylistSong.objects.filter(playlist=playlist).order_by('order')
        self.assertEqual(playlist_songs.count(), len(songs))

        sorted_songs = [song for order, song in sorted(zip(sorted_order, songs))]
        for playlist_song, song in zip(playlist_songs, sorted_songs):
            self.assertEqual(playlist_song.song, song)

    def test_update_playlist_song_to_left(self):
        playlist = self.create_playlist()

        for i in range(8):
            self.create_playlist_song(playlist=playlist)

        playlist_song = self.create_playlist_song(playlist=playlist, order=6)

        data = {
            'order': 3
        }

        response = self.client.patch(f'/playlist/{playlist.public_id}/order/{playlist_song.order}/',
                                     data,
                                     HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        playlist_songs = playlist.playlist_songs.all().order_by('order')

        for preferred_order, playlist_song in enumerate(playlist_songs, start=1):
            playlist_song = playlist_songs.filter(song=playlist_song.song).first()

            self.assertIsNotNone(playlist_song)
            self.assertEqual(playlist_song.order, preferred_order)

    def test_update_playlist_song_to_right(self):
        playlist = self.create_playlist()

        for i in range(8):
            self.create_playlist_song(playlist=playlist)

        playlist_song = self.create_playlist_song(playlist=playlist, order=3)

        data = {
            'order': 6
        }

        response = self.client.patch(f'/playlist/{playlist.public_id}/order/{playlist_song.order}/',
                                     data,
                                     HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        playlist_songs = playlist.playlist_songs.all().order_by('order')

        for preferred_order, playlist_song in enumerate(playlist_songs, start=1):
            playlist_song = playlist_songs.filter(song=playlist_song.song).first()

            self.assertIsNotNone(playlist_song)
            self.assertEqual(playlist_song.order, preferred_order)

    def test_update_song_pk(self):
        playlist = self.create_playlist()
        playlist_song = self.create_playlist_song(playlist=playlist)

        new_song = self.create_song()
        data = {
            'song_pk': new_song.public_id
        }
        response = self.client.patch(f'/playlist/{playlist.public_id}/order/{playlist_song.order}/',
                                     data,
                                     HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(PlaylistSong.objects.filter(playlist=playlist).first().song.pk,
                         playlist_song.song.pk,
                         'Song has changed')

    def test_delete_playlist_song(self):
        playlist = self.create_playlist()

        for i in range(3):
            self.create_playlist_song(playlist=playlist)

        playlist_song = self.create_playlist_song(playlist=playlist, order=2)

        response = self.client.delete(f'/playlist/{playlist.public_id}/order/{playlist_song.order}/',
                                      HTTP_AUTHORIZATION=f'Bearer {self.token}')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(PlaylistSong.objects.count(), 3)

        playlist_songs = playlist.playlist_songs.all()
        for preferred_order, playlist_song in enumerate(playlist_songs, start=1):
            playlist_song = playlist_songs.filter(song=playlist_song.song).first()

            self.assertIsNotNone(playlist_song)
            self.assertEqual(playlist_song.order, preferred_order)
