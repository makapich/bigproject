from .base import *

SECRET_KEY = '4yn7cqoefycnregqfqefe)fdsiuby!hfbijfi4f345cywumg8cnmro&uheo8cnoqo87'

DEBUG = True

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'blog',

]

ALLOWED_HOSTS = []

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
NOREPLY_EMAIL = 'noreply@baidygram.com'
CONTACT_EMAIL = 'contact@baidygram.com'
