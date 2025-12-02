from accounts.models import UserActivity

def log_activity(request, data):
    UserActivity.objects.create(
        user=request.user if request.user.is_authenticated else None,
        ip=request.META.get("REMOTE_ADDR"),
        action=data.get("action", "Unknown"),
        page_url=data.get("url"),
        raw_input=data.get("input") or str(data),
        threat_score=data.get("threatScore", 0)
    )
