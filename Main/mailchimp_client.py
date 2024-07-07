from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from mailchimp3 import MailChimp
from django.conf import settings

def get_mailchimp_client():
    return MailChimp(mc_api=settings.MAILCHIMP_API_KEY, mc_user='your-username', server=settings.MAILCHIMP_SERVER_PREFIX)


