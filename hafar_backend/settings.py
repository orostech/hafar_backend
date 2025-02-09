from datetime import timedelta
import os
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = config('DEBUG', default=False, cast=bool)


SECRET_KEY = config('SECRET_KEY')
ALLOWED_HOSTS = config('ALLOWED_HOSTS',cast=Csv())

# Application definition

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # APPS
    'rest_framework',
    'rest_framework_simplejwt',
    'channels',
    'storages',

    # HAFAR APPS
    'chat',
    'users',
    'match',
    'config',
    'notification'

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # ... other middleware ...
    # 'users.middleware.UpdateLastSeenMiddleware',
]



# DigitalOcean Spaces Configuration (for both static and media files) 
AWS_ACCESS_KEY_ID = config('DO_SPACES_KEY')
AWS_SECRET_ACCESS_KEY = config('DO_SPACES_SECRET')
AWS_STORAGE_BUCKET_NAME = config('DO_SPACES_BUCKET')
AWS_S3_ENDPOINT_URL = config('DO_SPACES_ENDPOINT')
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400', 'ACL': 'public-read'}
AWS_S3_CUSTOM_DOMAIN = config('DO_SPACES_CUSTOM_DOMAIN')




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
                "location": "hafar/media",  # Optional: where to store in the bucket
            },
    },
    "staticfiles": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
                "access_key": AWS_ACCESS_KEY_ID,
                "secret_key": AWS_SECRET_ACCESS_KEY,
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "location": "hafar/static", 
            },
    },
}
    # STATIC_URL = f'{AWS_S3_CUSTOM_DOMAIN}/hafar/static/'
    # MEDIA_URL = f'{AWS_S3_CUSTOM_DOMAIN}/hafar/media/'
else:
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'


STATIC_ROOT = os.path.join(BASE_DIR, 'static')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')



ROOT_URLCONF = 'hafar_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

    'EXCEPTION_HANDLER': 'chat.utils.custom_exception_handler'

}

SIMPLE_JWT = {
    'AUTH_HEADER_TYPES': ('JWT',),
    'ACCESS_TOKEN_LIFETIME': timedelta(days=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=20),
    #  'ACCESS_TOKEN_LIFETIME': timedelta(days=int(config('JWT_ACCESS_TOKEN_LIFETIME_DAYS', 1))),
    # 'REFRESH_TOKEN_LIFETIME': timedelta(days=int(config('JWT_REFRESH_TOKEN_LIFETIME_DAYS', 1))),
    'ROTATE_REFRESH_TOKENS': True,

}


# WSGI_APPLICATION = 'hafar_backend.wsgi.application'
ASGI_APPLICATION = 'hafar_backend.asgi.application'
# daphne -b 0.0.0.0 -p 8000 hafar_backend.asgi:application

CHANNEL_LAYERS = {
     "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
        # "BACKEND": "channels_redis.core.RedisChannelLayer",
        # "CONFIG": {
        #     "hosts": [(config('REDIS_URL', 'redis://localhost:6379/1'))],
        # },
    },
    # "default": {
    #     "BACKEND": "channels.layers.InMemoryChannelLayer",  # Use Redis in production
    # },
}




AUTH_USER_MODEL = 'users.user'

# Media configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB


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
