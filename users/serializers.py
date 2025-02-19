# serializers.py in your users app

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from .models import UserProfile

User = get_user_model()

class GroupSerializer(serializers.ModelSerializer):
    """
    Serializer for handling the Group model.
    Includes fields for the group's ID and name.
    """
    class Meta:
        model = Group
        fields = ['id', 'name']

class UserProfileSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    isSuperadmin = serializers.BooleanField(source='user.is_superuser', read_only=True)  # Add isSuperadmin
    user_id = serializers.IntegerField(source='user.id', read_only=True)  # Include user ID

    class Meta:
        model = UserProfile
        fields = ['id','user_id','first_name', 'last_name', 'email', 'bio', 'profile_picture', 'isSuperadmin']  # Include isSuperadmin

    def update(self, instance, validated_data):
        # Update user fields
        user_data = validated_data.pop('user', {})
        user = instance.user
        user.first_name = user_data.get('first_name', user.first_name)
        user.last_name = user_data.get('last_name', user.last_name)
        user.email = user_data.get('email', user.email)
        user.save()

        # Update profile fields
        instance.bio = validated_data.get('bio', instance.bio)
        instance.profile_picture = validated_data.get('profile_picture', instance.profile_picture)
        instance.save()

        return instance


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for handling the User model.
    Includes fields for user information, group management, superuser status, and user profile.
    """
    groups = GroupSerializer(many=True, required=False)  # Serialize groups associated with the user
    is_superuser = serializers.BooleanField(default=False)  # Field to manage superuser status
    profile = UserProfileSerializer(required=False)  # Include profile information

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'groups', 'is_superuser', 'profile']

    def create(self, validated_data):
        """
        Customize the user creation process.
        Handles group assignment, superuser status, and user profile.
        """
        groups_data = validated_data.pop('groups', [])
        profile_data = validated_data.pop('profile', {})
        is_superuser = validated_data.pop('is_superuser', False)

        user = User.objects.create_user(**validated_data)

        for group_data in groups_data:
            group, created = Group.objects.get_or_create(name=group_data['name'])
            user.groups.add(group)

        user.is_superuser = is_superuser
        user.save()

        UserProfile.objects.create(user=user, **profile_data)

        return user

    def update(self, instance, validated_data):
        """
        Customize the update process.
        Handles password updates, group management, superuser status, and user profile.
        """
        groups_data = validated_data.pop('groups', [])
        profile_data = validated_data.pop('profile', {})
        password = validated_data.pop('password', None)
        is_superuser = validated_data.pop('is_superuser', None)

        instance = super().update(instance, validated_data)  # Update the user fields

        if password:
            instance.set_password(password)
            instance.save()

        if groups_data:
            instance.groups.clear()
            for group_data in groups_data:
                group, created = Group.objects.get_or_create(name=group_data['name'])
                instance.groups.add(group)

        if is_superuser is not None:
            instance.is_superuser = is_superuser
            instance.save()

        # Update or create the user profile
        UserProfile.objects.update_or_create(user=instance, defaults=profile_data)

        return instance

class PublicUserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(source='profile.profile_picture', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'profile_picture']  # Add first_name, last_name, and profile_picture
