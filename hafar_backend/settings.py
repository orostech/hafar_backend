from datetime import timedelta
import json
import os
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# try:
#     FIREBASE_CREDENTIALS = json.loads(config('FIREBASE_CREDENTIALS'))
# except json.JSONDecodeError as e:
#     raise ValueError("Invalid JSON in FIREBASE_CREDENTIALS environment variable. Please check your .env file.") from e

DEBUG = config('DEBUG', default=False, cast=bool)




SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS',cast=Csv())


CORS_ALLOW_ALL_ORIGINS = DEBUG  # For development only


CORS_ALLOWED_ORIGINS = [
   "https://hafar-b5749.web.app",
#    "http://localhost:64975",
#    "https://2938-102-89-69-178.ngrok-free.app"
# # #     "http://127.0.0.1:8000",
# # #     "http://localhost",
# # #     "http://10.0.2.2:8000",    # Android emulator
]


FLUTTERWAVE_SECRET_KEY = config('FLUTTERWAVE_SECRET_KEY')

APP_PACKAGE_NAME= 'com.orostech.hafar'

# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.gis',

    # APPS
    'rest_framework',
     'corsheaders',
    'rest_framework_simplejwt',
    'channels',
    'storages',
    'drf_yasg',
    'drf_spectacular',
    'django_jsonform',
    'django_filters',
    'django_cryptography',
    
    # HAFAR APPS
    'chat',
    'config',
    'gift',
    'match',
    'notification',
    'subscription',    
    'users',
    'wallet'
]

MIDDLEWARE = [
      'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
  
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # ... other middleware ...
    'users.middleware.UpdateLastSeenMiddleware',
]

SERVER_DOMAIN = 'api.joinhafar.com'

# DigitalOcean Spaces Configuration (for both static and media files) 
AWS_ACCESS_KEY_ID = config('DO_SPACES_KEY')
AWS_SECRET_ACCESS_KEY = config('DO_SPACES_SECRET')
AWS_STORAGE_BUCKET_NAME = config('DO_SPACES_BUCKET')
AWS_S3_ENDPOINT_URL = config('DO_SPACES_ENDPOINT')
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400', 'ACL': 'public-read'}
AWS_S3_CUSTOM_DOMAIN = SERVER_DOMAIN
# config('DO_SPACES_CUSTOM_DOMAIN')




# Static files configuration
if not DEBUG:
    # Production settings
    STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
                "access_key": AWS_ACCESS_KEY_ID,
                "secret_key": AWS_SECRET_ACCESS_KEY,
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "location": "media",  # Optional: where to store in the bucket
            },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
                "access_key": AWS_ACCESS_KEY_ID,
                "secret_key": AWS_SECRET_ACCESS_KEY,
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "location": "static", 
            },
    },
}
    # STATIC_URL = f'{AWS_S3_CUSTOM_DOMAIN}/hafar/static/'
    # MEDIA_URL = f'{AWS_S3_CUSTOM_DOMAIN}/hafar/media/'
    # STATIC_URL = f'{AWS_S3_CUSTOM_DOMAIN}/static/'
    # MEDIA_URL = f'{AWS_S3_CUSTOM_DOMAIN}/media/'
    STATIC_URL = f'{SERVER_DOMAIN}/static/'
    MEDIA_URL = f'{SERVER_DOMAIN}/media/'
else:
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'


STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# MEDIA_URL = '/media/' 



ROOT_URLCONF = 'hafar_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,  # Set the default page size here
    'DEFAULT_THROTTLE_RATES': {
        'message': '10/minute',  # Adjust as needed
    },
    # 'DEFAULT_SCHEMA_CLASS': 'rest_framework.schemas.coreapi.AutoSchema', 
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    'EXCEPTION_HANDLER': 'chat.utils.custom_exception_handler'

}
SPECTACULAR_SETTINGS = {
    'TITLE': 'Hafar Social API',
    'DESCRIPTION': 'Hafae dating app',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # OTHER SETTINGS
}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=20),
    'ROTATE_REFRESH_TOKENS': True,

}


# WSGI_APPLICATION = 'hafar_backend.wsgi.application'
ASGI_APPLICATION = 'hafar_backend.asgi.application'
# daphne -b 0.0.0.0 -p 8000 hafar_backend.asgi:application

CHANNEL_LAYERS = {
     "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
 
    },
       #  'default': {
    #         'BACKEND': 'channels_redis.core.RedisChannelLayer',
    #         'CONFIG': {
    #             "hosts": [("redis", 6379)],
    #         },
    # },
    # "default": {
    #     "BACKEND": "channels.layers.InMemoryChannelLayer",  # Use Redis in production
    # },
}




AUTH_USER_MODEL = 'users.user'

# Media configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB



# if DEBUG:
#     SECURE_SSL_REDIRECT = False
#     SECURE_PROXY_SSL_HEADER = None
# else:
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_BEAT_SCHEDULE = {
    'expire_messages': {
        'task': 'chat.tasks.expire_temporary_messages',
        'schedule': 300,  # 5 minutes
    },
    'clean_chats': {
        'task': 'chat.tasks.clean_old_chats',
        'schedule': 86400,  # Daily
    },
    'push_notifications': {
        'task': 'chat.tasks.send_push_notifications',
        'schedule': 60,  # Every minute
    },
}

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True



# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

POSTMARK_API_KEY = config('POSTMARK_API_KEY')
DEFAULT_FROM_EMAIL = 'hafar.orostech@joinhafar.com'
FRONTEND_URL = 'https://joinhafar.com'
SITE_NAME = "Hafar"

# Firebase Configuration
FIREBASE_CONFIG = {
    "type": config('FIREBASE_TYPE'),
    "project_id": config('FIREBASE_PROJECT_ID'),
    "private_key_id": config('FIREBASE_PRIVATE_KEY_ID'),
    "private_key": config('FIREBASE_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": config('FIREBASE_CLIENT_EMAIL'),
    "client_id": config('FIREBASE_CLIENT_ID'),
    "auth_uri": config('FIREBASE_AUTH_URI'),
    "token_uri": config('FIREBASE_TOKEN_URI'),
    "auth_provider_x509_cert_url": config('FIREBASE_AUTH_PROVIDER_X509_CERT_URL'),
    "client_x509_cert_url": config('FIREBASE_CLIENT_X509_CERT_URL'),
    "universe_domain": config('FIREBASE_UNIVERSE_DOMAIN')
}
