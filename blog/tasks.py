from celery import shared_task

from django.core.mail import send_mail as django_send_mail


@shared_task
def send_mail(subject, message, from_email, to_email, html_message=None):
    django_send_mail(subject, message, from_email, to_email, html_message=html_message)
