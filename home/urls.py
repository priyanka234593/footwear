from django.urls import path
from .views import index, product_search, contact, about, terms_and_conditions, privacy_policy

urlpatterns = [
    path('', index, name="index"),
    path('search/', product_search, name="product_search"),
    path('contact/', contact, name="contact"),
    path('about/', about, name="about"),
    path('terms-and-conditions/', terms_and_conditions, name="terms-and-conditions"),
    path('privacy-policy/', privacy_policy, name="privacy-policy")

]
