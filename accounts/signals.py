from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.contrib.auth.models import User
from accounts.models import Profile
from accounts.utils import log_activity


# ------------------------
#  PROFILE AUTO CREATION
# ------------------------
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# ------------------------
#  LOGIN TRACKING
# ------------------------
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    data = {"action": "Login", "url": request.path, "input": "", "threatScore": 0}
    log_activity(request, data)

