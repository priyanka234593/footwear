from django.urls import path
from .views import (
    RegisterAPI, LoginAPI, ProfileAPI, LogoutAPI,
    ForgotPasswordAPI, ResetPasswordAPI, ActivateAccountAPI
)

urlpatterns = [
    path("register/", RegisterAPI.as_view(), name="register"),
    path("login/", LoginAPI.as_view(), name="login"),
    path("profile/", ProfileAPI.as_view(), name="profile"),
    path("logout/", LogoutAPI.as_view(), name="logout"),

    # Forgot / Reset System — WITH names
    path("forgot-password/", ForgotPasswordAPI.as_view(), name="forgot_password"),
    path("reset-password/<str:token>/", ResetPasswordAPI.as_view(), name="reset_password"),

    # Email activation
    path("activate/<str:token>/", ActivateAccountAPI.as_view(), name="activate_account"),
]


