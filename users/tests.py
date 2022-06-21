import os.path

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from vibly import settings


class UserCreate:
    @staticmethod
    def get_token(client, email, password):
        response = client.post('/auth/token/', {'email': email, 'password': password})
        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            raise Exception('Something wrong')

        return response.data['access']

    @classmethod
    def create_user_dict(cls, client, **kwargs):
        username = 'test'
        if get_user_model().objects.filter(username=username).exists():
            username += '_'

        email = 'test@email.com'
        if get_user_model().objects.filter(email=email).exists():
            email += '_'

        data = {
            'username': username,
            'email': email,
            'password': 'testpass123',
        }

        data.update(**kwargs)

        user = get_user_model().objects.create_user(**data)
        return {
            'user': user,
            'token': cls.get_token(client,
                                   user.email,
                                   data.get('password')),
            'raw_password': data.get('password')
        }


class UserTests(APITestCase):
    def setUp(self):
        def end():
            for user in get_user_model().objects.all():
                user.delete()

        self.addCleanup(end)

    def create_user_dict(self, **kwargs):
        return UserCreate.create_user_dict(self.client, **kwargs)

    def test_create_user(self):
        data = {
            'username': 'testuser2',
            'email': 'test2@email.com',
            'password': 'testpass123',
        }
        response = self.client.post('/user/', data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email='test2@email.com')
        self.assertEqual(user.username, 'testuser2')
        self.assertEqual(user.email, 'test2@email.com')
        self.assertNotEqual(user.password, 'testpass123', 'Password hasn\'t been hashed')

    def test_create_user_with_pfp(self):
        pfp_url = os.path.join(os.path.abspath(os.path.dirname(__name__)), 'testfiles/armstrong.jpg')
        pfp = open(pfp_url, 'rb')
        data = {
            'username': 'testuser2pfp',
            'email': 'test2pfp@email.com',
            'password': 'testpass123',
            'pfp': pfp
        }
        response = self.client.post('/user/', data)

        default_url = os.path.join(os.path.abspath(os.path.dirname(__name__)),
                                   settings.MEDIA_ROOT,
                                   get_user_model().pfp.field.default)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email='test2pfp@email.com')
        self.assertEqual(user.username, 'testuser2pfp')
        self.assertEqual(user.email, 'test2pfp@email.com')
        self.assertNotEqual(user.password, 'testpass123', 'Password hasn\'t been hashed')
        self.assertEqual(user.pfp.url, f'/{response.data.get("pfp").split("/", 3)[-1]}')
        self.assertTrue(os.path.exists(default_url), 'Default pfp not found. '
                                                     'Probably has been deleted by vibly/img.py')

    def test_password_validation(self):
        data = {
            'username': 'testuser3',
            'email': 'test3@email.com',
            'password': 't',
        }
        response = self.client.post('/user/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user(self):
        user_dict = self.create_user_dict()
        user = user_dict.get('user')
        token = user_dict.get('token')

        response = self.client.get('/user/', HTTP_AUTHORIZATION=f'Bearer {token}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], user.username)
        self.assertEqual(response.data['email'], user.email)

    def test_retrieve_other_user(self):
        user = self.create_user_dict().get('user')
        response = self.client.get(f'/user/{user.public_id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], user.username)
        self.assertEqual(response.data['email'], user.email)

    def test_update_user(self):
        user_dict = self.create_user_dict()
        token = user_dict.get('token')
        user = user_dict.get('user')

        data = {
            'username': 'testuseredited',
            'email': 'test@emailedited.com',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.put('/user/', data, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        created_user = get_user_model().objects.filter(
            email=user.email
        ).first()

        self.assertIsNotNone(created_user, 'Email has probably changed')
        self.assertNotEqual(created_user.username, data['username'], 'Username has changed')
        self.assertNotEqual(created_user.email, data['email'], 'Email has changed')
        self.assertEqual(created_user.first_name, data['first_name'])
        self.assertEqual(created_user.last_name, data['last_name'])

    def test_pfp(self):
        user_dict = self.create_user_dict()
        user = user_dict.get('user')
        token = user_dict.get('token')

        pfp_url = os.path.join(os.path.abspath(os.path.dirname(__name__)), 'testfiles/armstrong.jpg')
        pfp = open(pfp_url, 'rb')
        response = self.client.patch('/user/', {'pfp': pfp}, HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = get_user_model().objects.get(id=user.id)
        self.assertNotEqual(user.pfp.name.split('/')[-1],
                            user.pfp.field.default.split('/')[-1],
                            'Pfp hasn\'t changed')

        default_url = os.path.join(os.path.abspath(os.path.dirname(__name__)),
                                   settings.MEDIA_ROOT,
                                   user.pfp.field.default)

        self.assertTrue(os.path.exists(default_url), 'Default pfp not found. '
                                                     'Probably has been deleted by vibly/img.py')

    def test_delete_user(self):
        user_dict = self.create_user_dict()
        token = user_dict.get('token')
        user = user_dict.get('user')

        response = self.client.delete('/user/', HTTP_AUTHORIZATION=f'Bearer {token}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(get_user_model().objects.filter(email=user.email).exists(), 'User hasn\'t been deleted')
