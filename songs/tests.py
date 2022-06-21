import datetime

from django.core.files import File
from rest_framework import status
from rest_framework.test import APITestCase
from mutagen.mp3 import MP3
from PIL import Image

from .models import Song
from users.tests import UserCreate


class SongCreate:
    @staticmethod
    def create_song(client, token, **kwargs):
        song_file = File(open('testfiles/Among Us Drip Theme Song Original.mp3', 'rb'))
        cover = File(open('testfiles/armstrong.jpg', 'rb'))

        data = {
            'title': 'test song',
            'song_file': song_file,
            'cover': cover,
            'public': True
        }

        data.update(kwargs)

        song = client.post('/song/', data, HTTP_AUTHORIZATION=f'Bearer {token}')
        return Song.objects.filter(pk=song.data.get('id')).first()


class SongTests(APITestCase):
    def setUp(self):
        user_dict = UserCreate.create_user_dict(self.client)
        self.user = user_dict.get('user')
        self.token = user_dict.get('token')

        def end():
            for song in Song.objects.all():
                song.delete()

        self.addCleanup(end)

    def create_song(self, **kwargs):
        return SongCreate.create_song(self.client, self.token, **kwargs)

    def test_create_song(self):
        song_file = open('testfiles/Among Us Drip Theme Song Original.mp3', 'rb')
        cover = open('testfiles/armstrong.jpg', 'rb')

        data = {
            'title': 'test song',
            'song_file': song_file,
            'cover': cover,
            'public': True
        }

        response = self.client.post('/song/', data, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Song.objects.count(), 1)

        song = Song.objects.filter(public_id=response.data.get('public_id')).first()
        self.assertEqual(song.title, 'test song')
        self.assertEqual(song.author, self.user)
        self.assertTrue(song.song_file is not None)
        self.assertTrue(song.cover is not None)
        self.assertTrue(song.public)

        song_file_duration = MP3(song_file).info.length
        self.assertEqual(song.duration, datetime.timedelta(seconds=song_file_duration))

        cover_image = Image.open(song.cover)
        self.assertEqual(cover_image.size, (512, 512))

    def test_create_bad_song(self):
        song_file = File(open('testfiles/definitelynotmp3.mp3', 'rb'))

        data = {
            'title': 'test song',
            'song_file': song_file,
            'public': True
        }

        response = self.client.post('/song/', data, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_song(self):
        song = self.create_song()

        response = self.client.get(f'/song/{song.public_id}/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('id'), song.id)
        self.assertEqual(response.data.get('title'), song.title)
        self.assertEqual(response.data.get('author').get('id'), song.author.id)
        self.assertEqual(response.data.get('public'), song.public)
        self.assertEqual(response.data.get('duration')[1:], str(song.duration))
        self.assertEqual(response.data.get('created_at'), song.created_at.isoformat())

    def test_retrieve_unpublished_song(self):
        song = self.create_song(public=False)

        response = self.client.get(f'/song/{song.public_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_song(self):
        song = self.create_song()

        data = {
            'title': 'updated song',
            'public': False
        }

        response = self.client.patch(f'/song/{song.public_id}/', data, HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        song = Song.objects.filter(pk=song.id).first()
        self.assertEqual(song.title, 'updated song')
        self.assertFalse(song.public)

    def test_destroy_song(self):
        song = self.create_song()

        response = self.client.delete(f'/song/{song.public_id}/', HTTP_AUTHORIZATION=f'Bearer {self.token}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Song.objects.count(), 0)
