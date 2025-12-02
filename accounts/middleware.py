from accounts.utils import log_activity

class UniversalTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        response = self.get_response(request)

        # Ignore noise (admin + static)
        if request.path.startswith("/admin") or request.path.startswith("/static"):
            return response

        action = "Page Visit"
        data_input = None

        # Detect search
        if request.GET.get("q"):
            action = "Search Query"
            data_input = request.GET.get("q")

        # Detect form submissions
        if request.method == "POST":
            action = "Form Submit"
            try:
                data_input = request.body.decode()[:300]  # protect from large payloads
            except:
                data_input = None

        # Detect login/logout/cart automatically from URL
        keywords = {
            "login": "Login Event",
            "logout": "Logout Event",
            "cart": "Cart Event",
            "checkout": "Checkout Event",
        }

        for key, act in keywords.items():
            if key in request.path.lower():
                action = act
                break

        # Save activity
        log_activity(request, {
            "action": action,
            "url": request.path,
            "input": data_input,
            "threatScore": 0
        })

        return response
