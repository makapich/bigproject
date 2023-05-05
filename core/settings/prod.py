from .base import *
import cloudinary, cloudinary_storage

SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = False

INSTALLED_APPS = [
    'whitenoise.runserver_nostatic',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cloudinary_storage',
    'cloudinary',
    'debug_toolbar',
    'blog',

]

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'your_cloud_name',
    'API_KEY': 'your_api_key',
    'API_SECRET': 'your_api_secret'
}

ALLOWED_HOSTS = ['EXTERNAL SERVER IP', 'DOMAIN NAME', 'ANOTHER DOMAIN NAME ETC']

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your email'
EMAIL_HOST_PASSWORD = 'password'
NOREPLY_EMAIL = 'noreply email'
CONTACT_EMAIL = 'contact email'
