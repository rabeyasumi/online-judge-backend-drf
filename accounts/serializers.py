
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction

from rest_framework import serializers

from .models import Student


User = get_user_model()


class RegisterSerializer(serializers.Serializer):

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False
    )
    name = serializers.CharField(max_length=100)
    handle = serializers.CharField(max_length=50)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "This username is already taken."
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "This email is already registered."
            )
        return value

    def validate_handle(self, value):
        if Student.objects.filter(handle__iexact=value).exists():
            raise serializers.ValidationError(
                "This handle is already taken."
            )
        return value

    def validate_password(self, value):
        validate_password(value)
        return value

    @transaction.atomic
    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        student = Student.objects.create(
            user=user,
            name=validated_data['name'],
            handle=validated_data['handle']
        )

        return student
    

class ProfileUpdateSerializer(serializers.Serializer):

    name = serializers.CharField(max_length=100, required=False)
    email = serializers.EmailField(required=False)

    def validate_email(self, value):
        user = self.context['request'].user

        if User.objects.filter(
            email__iexact=value
        ).exclude(id=user.id).exists():

            raise serializers.ValidationError(
                "This email is already registered."
            )

        return value

    def update(self, instance, validated_data):

        user = instance
        student = getattr(user, 'student_profile', None)

        if 'email' in validated_data:
            user.email = validated_data['email']
            user.save(update_fields=['email'])

        if 'name' in validated_data:
            if student is None:
                raise serializers.ValidationError({
                    'name': 'Student profile not found.'
                })

            student.name = validated_data['name']
            student.save(update_fields=['name'])

        return user


class ChangePasswordSerializer(serializers.Serializer):

    current_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False
    )

    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        trim_whitespace=False
    )

    confirm_password = serializers.CharField(
        write_only=True,
        trim_whitespace=False
    )

    def validate(self, attrs):

        user = self.context['request'].user

        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError({
                'current_password': 'Current password is incorrect.'
            })

        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({
                'confirm_password': 'New passwords do not match.'
            })

        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                'new_password': 'New password must be different from current password.'
            })

        validate_password(attrs['new_password'], user=user)

        return attrs

    def save(self, **kwargs):

        user = self.context['request'].user

        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])

        return user
