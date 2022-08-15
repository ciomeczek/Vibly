from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from vibly.img import reshape_and_return_url, delete_image


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['public_id', 'username', 'email', 'first_name', 'last_name', 'pfp']
        read_only_fields = ['id', 'username', 'email']

    def validate_password(self, password):
        try:
            validate_password(password)
        except ValueError as e:
            raise serializers.ValidationError(e)
        return password

    def save(self, **kwargs):
        # Removing pfp from validated_data, so it doesn't get saved classical way
        pfp = self.validated_data.get('pfp')
        self.validated_data.pop('pfp', None)

        if pfp:
            if self.instance:
                delete_image(self.instance.pfp)

            self.validated_data['pfp'] = reshape_and_return_url(pfp,
                                                                pfp.name,
                                                                self.Meta.model.pfp.field.upload_to,
                                                                height=512,
                                                                width=512)

        return super().save(**kwargs)

    def create(self, validated_data):
        user = get_user_model().objects.create_user(**validated_data)
        return user


class CreateUserSerializer(UserSerializer):
    class Meta:
        model = get_user_model()
        fields = ['public_id', 'username', 'password', 'email', 'first_name', 'last_name', 'pfp', 'public_id']
        extra_kwargs = {'password': {'write_only': True}}
