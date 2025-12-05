from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate, logout, login as auth_login
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string

from ..models import Profile
from .serializers import RegisterSerializer, LoginSerializer, UserProfileSerializer
from accounts.utils import send_account_activation_email, send_password_reset_email
from rest_framework.views import APIView
from rest_framework import status
from accounts.models import Profile


# ---------------- REGISTER ----------------

class RegisterAPI(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send activation email
        send_account_activation_email(user.email, user.profile.email_token)

        return Response({"message": "Account created. Check email to activate."}, status=201)



# ---------------- ACTIVATE ACCOUNT ----------------

class ActivateAccountAPI(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        profile = Profile.objects.filter(email_token=token).first()

        if not profile:
            return Response({"detail": "Invalid or expired activation link"}, status=status.HTTP_400_BAD_REQUEST)

        profile.is_email_verified = True
        profile.email_token = None
        profile.save()

        return Response({"message": "Account activated successfully!"}, status=status.HTTP_200_OK)


# ---------------- LOGIN ----------------

class LoginAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        identifier = request.data.get("email")
        password = request.data.get("password")

        user = (
            User.objects.filter(email=identifier).first()
            or User.objects.filter(username=identifier).first()
        )

        if not user:
            return Response({"detail": "Invalid credentials"}, status=400)

        if not user.profile.is_email_verified:
            return Response({"detail": "Email not verified"}, status=403)

        authenticated_user = authenticate(username=user.username, password=password)
        if not authenticated_user:
            return Response({"detail": "Invalid password"}, status=400)

        auth_login(request, authenticated_user)
        refresh = RefreshToken.for_user(authenticated_user)

        return Response({
            "message": "Login successful",
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserProfileSerializer(authenticated_user).data
        })


# ---------------- PROFILE ----------------

class ProfileAPI(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


# ---------------- LOGOUT ----------------

class LogoutAPI(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({"message": "Logged out successfully"})


# ---------------- RESET PASSWORD ----------------

class ForgotPasswordAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"detail": "User not found"}, status=404)

        token = get_random_string(50)
        user.profile.email_token = token
        user.profile.save()

        send_password_reset_email(email, token)

        return Response({"message": "Password reset link sent"})


class ResetPasswordAPI(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def post(self, request, token):
        profile = Profile.objects.filter(email_token=token).first()
        if not profile:
            return Response({"detail": "Invalid token"}, status=400)

        password = request.data.get("password")
        confirm = request.data.get("confirm_password")

        if password != confirm:
            return Response({"detail": "Passwords do not match"}, status=400)

        profile.user.set_password(password)
        profile.user.save()
        profile.email_token = None
        profile.save()

        return Response({"message": "Password updated successfully"})
