import os
import json
import uuid
from weasyprint import CSS, HTML
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth import views as auth_views

from accounts.models import Profile, Cart, CartItem, Order, OrderItem
from accounts.forms import UserUpdateForm, UserProfileForm, ShippingAddressForm, CustomPasswordChangeForm
from home.models import ShippingAddress
from base.emails import send_account_activation_email
from products.models import Product, SizeVariant


# ============================ AUTH ============================

def login_page(request):
    next_url = request.GET.get('next')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username=username).first()

        if not user_obj:
            messages.warning(request, "Account not found!")
            return redirect(request.path_info)

        if not user_obj.profile.is_email_verified:
            messages.error(request, "Verify your email before login.")
            return redirect(request.path_info)

        user_obj = authenticate(username=username, password=password)

        if user_obj:
            login(request, user_obj)
            messages.success(request, "Logged in successfully.")

            if next_url and url_has_allowed_host_and_scheme(url=next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)

            return redirect("index")

        messages.error(request, "Invalid credentials.")
        return redirect(request.path_info)

    return render(request, 'accounts/login.html')


def register_page(request):
    if request.method == "POST":
        username = request.POST.get("username")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            messages.warning(request, "Username already exists.")
            return redirect(request.path_info)

        if User.objects.filter(email=email).exists():
            messages.warning(request, "Email already registered.")
            return redirect(request.path_info)

        user = User.objects.create(
            username=username, first_name=first_name, last_name=last_name, email=email
        )
        user.set_password(password)
        user.save()

        profile = Profile.objects.get(user=user)
        profile.email_token = str(uuid.uuid4())
        profile.save()

        send_account_activation_email(email, profile.email_token)

        messages.success(request, "Verification email sent. Check inbox.")
        return redirect(request.path_info)

    return render(request, 'accounts/register.html')


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, "Logged out.")
    return redirect("index")


# ============================ EMAIL ACTIVATION ============================

def activate_email_account(request, email_token):
    try:
        profile = Profile.objects.get(email_token=email_token)

        if profile.is_email_verified:
            messages.info(request, "Account already verified. Login now.")
            return redirect("login")

        profile.is_email_verified = True
        profile.email_token = None
        profile.save()

        messages.success(request, "Email verified successfully. Login now.")
        return redirect("login")

    except Profile.DoesNotExist:
        messages.error(request, "Invalid or expired activation link.")
        return redirect("register")


# ============================ PASSWORD ============================

@login_required
def change_password(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)

        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully.")
            return redirect("profile", username=request.user.username)

        messages.error(request, "Fix errors and try again.")
    else:
        form = CustomPasswordChangeForm(request.user)

    return render(request, "accounts/change_password.html", {'form': form})


# ============================ CART ============================

@login_required
def add_to_cart(request, uid):
    variant = request.GET.get("size")

    if not variant:
        messages.warning(request, "Select a size first.")
        return redirect(request.META.get("HTTP_REFERER"))

    product = get_object_or_404(Product, uid=uid)
    cart, _ = Cart.objects.get_or_create(user=request.user, is_paid=False)
    size_variant = get_object_or_404(SizeVariant, size_name=variant)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, product=product, size_variant=size_variant
    )

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    messages.success(request, "Added to cart.")
    return redirect("cart")


@require_POST
@login_required
def update_cart_item(request):
    try:
        data = json.loads(request.body)
        item_id = data.get("cart_item_id")
        qty = int(data.get("quantity"))

        item = CartItem.objects.get(uid=item_id, cart__user=request.user, cart__is_paid=False)
        item.quantity = qty
        item.save()

        return JsonResponse({"success": True})
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


@login_required
def cart(request):
    user_cart = Cart.objects.filter(is_paid=False, user=request.user).first()

    if not user_cart:
        messages.warning(request, "Your cart is empty.")
        return redirect("index")

    if request.method == "POST":
        request.session["dummy_payment"] = True
        return redirect("success")

    return render(request, "accounts/cart.html", {
        "cart": user_cart,
        "quantity_range": range(1, 6)
    })


# ============================ PAYMENT SUCCESS ============================

def success(request):
    order_id = request.session.get("order_id")

    if not order_id:
        return redirect("index")

    order = Order.objects.filter(order_id=order_id).first()

    return render(request, "payment_success/payment_success.html", {
        "order_id": order_id,
        "order": order
    })


# ============================ USER PROFILE ============================

@login_required
def profile_view(request, username):
    user_obj = get_object_or_404(User, username=username)

    user_form = UserUpdateForm(instance=user_obj)
    profile_form = UserProfileForm(instance=user_obj.profile)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=user_obj)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=user_obj.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile", username=username)

    return render(request, "accounts/profile.html", {
        "user_name": user_obj,
        "user_form": user_form,
        "profile_form": profile_form
    })


@login_required
def update_shipping_address(request):
    address = ShippingAddress.objects.filter(user=request.user, current_address=True).first()

    if request.method == "POST":
        form = ShippingAddressForm(request.POST, instance=address)

        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            addr.current_address = True
            addr.save()

            messages.success(request, "Address updated.")
            return redirect("profile", username=request.user.username)

    else:
        form = ShippingAddressForm(instance=address)

    return render(request, "accounts/shipping_address_form.html", {'form': form})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by("-order_date")
    return render(request, "accounts/order_history.html", {"orders": orders})


@login_required
def delete_account(request):
    if request.method == "POST":
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Account deleted.")
        return redirect("index")

    return redirect("profile")


@login_required
def remove_cart(request, uid):
    try:
        item = CartItem.objects.get(uid=uid, cart__user=request.user, cart__is_paid=False)
        item.delete()
        messages.success(request, "Item removed.")

    except:
        messages.error(request, "Something went wrong.")

    return redirect(request.META.get("HTTP_REFERER", "cart"))


@login_required
def remove_coupon(request, cart_id):
    try:
        cart = Cart.objects.get(uid=cart_id, user=request.user, is_paid=False)
        cart.coupon = None
        cart.save()
        messages.success(request, "Coupon removed.")
    except:
        messages.error(request, "Failed to remove coupon.")

    return redirect(request.META.get("HTTP_REFERER", "cart"))


def order_details(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    return render(request, "order/order_details.html", {"order": order})
