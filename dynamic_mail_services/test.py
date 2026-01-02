from django.core.mail import send_mail
from django.http import HttpResponse
from django.conf import settings

def test_send_email(request):
    subject = "Test Email from Django"
    message = "This is a test email sent from Django views."
    from_email = settings.EMAIL_HOST_USER  # Ensure this is set in your settings.py
    recipient_list = ['khabindratamang7@gmail.com']  # Replace with your test email

    try:
        send_mail(subject, message, from_email, recipient_list)
        return HttpResponse("Email sent successfully!")
    except Exception as e:
        return HttpResponse(f"Failed to send email: {str(e)}")