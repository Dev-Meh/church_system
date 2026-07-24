from rest_framework import serializers
from .models import ChurchUser
from .registration_checks import (
    member_with_email_exists,
    member_with_identity_exists,
    member_with_phone_exists,
)

class ChurchUserSerializer(serializers.ModelSerializer):
    """Serializer for ChurchUser model"""
    class Meta:
        model = ChurchUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 
                 'phone_number', 'date_of_birth', 'gender', 'address', 
                 'city', 'country', 'postal_code', 'marital_status', 
                 'occupation', 'membership_date', 'role', 'is_active_member',
                 'date_joined', 'last_login']
        read_only_fields = ['id', 'membership_date', 'date_joined', 'last_login']

class ChurchUserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new ChurchUser"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = ChurchUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 
                 'password_confirm', 'phone_number', 'date_of_birth', 'gender', 
                 'address', 'city', 'country', 'postal_code', 'marital_status', 
                 'occupation']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")

        email = (attrs.get('email') or '').strip()
        if email and member_with_email_exists(email):
            raise serializers.ValidationError({'email': 'This email is already registered.'})

        phone = (attrs.get('phone_number') or '').strip()
        if phone and member_with_phone_exists(phone):
            raise serializers.ValidationError({'phone_number': 'This phone number is already registered.'})

        if member_with_identity_exists(
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
            date_of_birth=attrs.get('date_of_birth'),
        ):
            raise serializers.ValidationError(
                'A member with this name and date of birth is already registered.'
            )
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = ChurchUser.objects.create_user(
            password=password,
            role='member',
            is_active_member=False,
            **validated_data
        )
        return user
