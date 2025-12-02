from django.db.models import Q
from django.shortcuts import render
from products.models import Product, Category
import logging

# Create logger for monitoring firewall payloads
logger = logging.getLogger("WAF_TEST")

def index(request):
    query = Product.objects.all()
    categories = Category.objects.all()
    selected_sort = request.GET.get('sort')
    selected_category = request.GET.get('category')

    if selected_category:
        query = query.filter(category__category_name__icontains=selected_category)

    if selected_sort:
        if selected_sort == 'newest':
            query = query.filter(newest_product=True).order_by('category_id')
        elif selected_sort == 'priceAsc':
            query = query.order_by('price')
        elif selected_sort == 'priceDesc':
            query = query.order_by('-price')

    context = {
        'products': query,
        'categories': categories,
        'selected_category': selected_category,
        'selected_sort': selected_sort,
    }
    return render(request, 'home/index.html', context)


def product_search(request):
    query = request.GET.get('q', '')

    # Log raw payload for WAF monitoring
    logger.warning(f"[WAF TEST PAYLOAD] => {query}")

    # Search logic (still works normally)
    products = Product.objects.filter(
        Q(product_name__icontains=query) |
        Q(category__category_name__icontains=query) |
        Q(size_variant__size_name__icontains=query) |
        Q(color_variant__color_name__icontains=query)
    ).distinct()

    # return raw payload without escaping
    return render(request, 'home/search.html', {
        "query_raw": query,  # RAW payload for display
        "products": products
    })


def contact(request):
    return render(request, 'home/contact.html')

def about(request):
    return render(request, 'home/about.html')

def terms_and_conditions(request):
    return render(request, 'home/terms_and_conditions.html')

def privacy_policy(request):
    return render(request, 'home/privacy_policy.html')
