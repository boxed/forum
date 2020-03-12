"""
Django settings for forum2 project.

Generated by 'django-admin startproject' using Django 2.1.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
# import jinja2
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '#_26$$trs=(9en(wh6wc*+4nvh7n0d2t0b#mluna_=uea5k4*6'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'forum.kodare.com',
    'forum.killingar.net',
    '127.0.0.1',
    'localhost',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'forum',
    'unread',
    'wiki',
    'authentication',
    'issues',
    'tri_form',
    'tri_query',
    'tri_table',
    'django_user_agents',
    'iommi',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_user_agents.middleware.UserAgentMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'forum2.current_request_middleware',
    'forum2.ProfileMiddleware',
    'forum2.LoggingMiddleware',
    'forum2.login_middleware',
    'iommi.middleware',
]

ROOT_URLCONF = 'forum2.urls'

TEMPLATES = [
    # {
    #     'BACKEND': 'django.template.backends.jinja2.Jinja2',
    #     'DIRS': [],
    #     'APP_DIRS': True,
    #     'OPTIONS': {
    #         'undefined': jinja2.StrictUndefined,
    #         'context_processors': [
    #             'django.template.context_processors.debug',
    #             'django.template.context_processors.request',
    #             'django.contrib.auth.context_processors.auth',
    #             'django.contrib.messages.context_processors.messages',
    #         ],
    #     },
    # },
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
            'string_if_invalid': 'DEBUG WARNING: undefined template variable [%s] not found'
        },
    },
]

WSGI_APPLICATION = 'forum2.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'forum',
        'USER': os.environ.get('DOKKU_MYSQL_MYSQL_ENV_MYSQL_USER', 'root'),
        'PASSWORD': os.environ.get('DOKKU_MYSQL_MYSQL_ENV_MYSQL_PASSWORD', ''),
        'HOST': os.environ.get('DOKKU_MYSQL_MYSQL_PORT_3306_TCP_ADDR', '127.0.0.1'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': 'set collation_connection=utf8mb4_unicode_ci; SET sql_mode=\'STRICT_TRANS_TABLES\'',
        },
    }
}

X_FRAME_OPTIONS = 'ALLOW-FROM https://forum.kodare.com/'

# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = False

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = Path(__file__).parent.parent / 'static/'


# AUTH_USER_MODEL = 'forum.User'

DATETIME_FORMAT = 'Y-m-d H:i:s'

DATE_FORMAT = 'Y-m-d'

INSTALLATION_NAME = 'SKForum'
NO_REPLY_EMAIL = 'no-reply@killingar.net'

X_FRAME_OPTIONS = 'sameorigin'

IOMMI_DEFAULT_STYLE = 'forum'

try:
    from .settings_local import *
except ImportError:
    pass

if not DEBUG:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn="https://cc753814601047d695eae69e4b366c48@sentry.io/1415562",
        integrations=[DjangoIntegration()]
    )
