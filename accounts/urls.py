from django.urls import path
from accounts.views import (
    login_page, register_page, user_logout, activate_email_account,
    change_password, add_to_cart, update_cart_item, cart, success,
    profile_view, update_shipping_address, order_history,
    delete_account, remove_cart, remove_coupon, order_details
)
from django.contrib.auth import views as auth_views

urlpatterns = [

    # -------- AUTH --------
    path('login/', login_page, name="login"),
    path('register/', register_page, name="register"),
    path('logout/', user_logout, name="logout"),

    path('activate/<str:email_token>/', activate_email_account, name="activate"),


    # -------- USER PROFILE AREA --------
    path('profile/<str:username>/', profile_view, name='profile'),
    path('change-password/', change_password, name='change_password'),
    path('shipping-address/', update_shipping_address, name='shipping-address'),  # <-- restored


    # -------- PASSWORD RESET FLOW --------
   path(
    'password_reset/',
    auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset_form.html',
        email_template_name='registration/password_reset_email.html',
        html_email_template_name='registration/password_reset_email.html',  # <-- THIS IS REQUIRED
        subject_template_name='registration/password_reset_subject.txt',
    ),
    name='password_reset'
),

    path(
        'password_reset_done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='registration/password_reset_done.html'
        ),
        name='password_reset_done'
    ),

    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='registration/password_reset_confirm.html'
        ),
        name='password_reset_confirm'
    ),

    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='registration/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),


    # -------- CART --------
    path('cart/', cart, name="cart"),
    path('add-to-cart/<uid>/', add_to_cart, name="add_to_cart"),
    path('update_cart_item/', update_cart_item, name='update_cart_item'),
    path('remove-cart/<uid>/', remove_cart, name="remove_cart"),
    path('remove-coupon/<cart_id>/', remove_coupon, name="remove_coupon"),


    # -------- ORDER & PAYMENT --------
    path('success/', success, name="success"),
    path('order-history/', order_history, name='order_history'),
    path('order/<str:order_id>/', order_details, name='order_details'),
    path('delete-account/', delete_account, name='delete_account'),
]
