from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_account_activation_email(email, email_token):
    subject = "Verify Your FootFusion Account"
    sender = settings.DEFAULT_FROM_EMAIL

    # Ensure BASE_URL exists or fallback to localhost:3000
    base_url = getattr(settings, "BASE_URL", "http://127.0.0.1:3000")

    # Final activation URL (must match Django route)
    activation_link = f"{base_url}/accounts/activate/{email_token}/"

    # Render HTML email template
    html_content = render_to_string(
        "emails/account_activation.html", 
        {"activation_link": activation_link}
    )

    # Plain text fallback
    text_content = f"""
Hi,

Thanks for signing up!

Please verify your account by clicking the link below:

{activation_link}

If you did not request this, ignore this email.

Regards,  
FootFusion Team
"""

    send_mail(
        subject,
        text_content.strip(),
        sender,
        [email],
        html_message=html_content
    )
