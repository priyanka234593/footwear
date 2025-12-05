from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from accounts.models import Profile


# -------------------- REGISTER --------------------
class RegisterSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password"]

    def validate(self, data):
        email = data["email"].lower()

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "This email is already registered."})

        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError({"username": "This username is already taken."})

        data["email"] = email  # Normalize email
        return data

    def create(self, validated_data):
        from accounts.utils import send_account_activation_email

        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()

        # Generate activation token
        token = get_random_string(50)

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.email_token = token
        profile.is_email_verified = False
        profile.save()

        # Send verification email
        send_account_activation_email(user.email, token)

        return user


# -------------------- LOGIN --------------------
class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data["email"].lower()

        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "No account found with this email."})

        user = User.objects.get(email=email)

        if not user.check_password(data["password"]):
            raise serializers.ValidationError({"password": "Incorrect password."})

        if not user.profile.is_email_verified:
            raise serializers.ValidationError({"detail": "Please verify your email before logging in."})

        data["user"] = user
        return data


# -------------------- USER PROFILE --------------------
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]
