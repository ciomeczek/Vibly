from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from vibly.img import reshape_and_return_url, delete_image


class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'password', 'email', 'first_name', 'last_name', 'pfp']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'pfp']
        read_only_fields = ['id', 'username']

    def save(self, **kwargs):
        # Removing pfp from validated_data, so it doesn't get saved classical way
        pfp = self.validated_data.get('pfp')
        self.validated_data.pop('pfp', None)

        if self.validated_data.get('password'):
            self.validated_data['password'] = make_password(self.validated_data['password'])

        if pfp:
            if self.instance:
                delete_image(self.instance.pfp)

            self.validated_data['pfp'] = reshape_and_return_url(pfp,
                                                                pfp.name,
                                                                self.Meta.model.pfp.field.upload_to,
                                                                height=128,
                                                                width=128)

        return super().save(**kwargs)
