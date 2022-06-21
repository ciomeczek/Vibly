from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import CustomUserManager


class CustomUser(AbstractUser):
    username = models.CharField(max_length=30, unique=False, blank=False, null=False)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True, max_length=500)
    pfp = models.ImageField(upload_to='pfps/', default='defaults/pfps/default.png', blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    def __str__(self):
        return self.email

    def delete(self, using=None, keep_parents=False):
        if self.pfp.name != self.pfp.field.default:
            self.pfp.delete()
        return super().delete(using, keep_parents)
