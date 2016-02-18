"""
Django settings for chillpublic project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import getpass
import djcelery
djcelery.setup_loader()
from celery.schedules import crontab

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

BROKER_URL = 'amqp://guest:guest@localhost:5672/'

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'rhp&(6plb8z4rfgy2)s!d_nupbw#1^p=$et5q+2y+q&ds1w3m%'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

TEMPLATE_DIRS = (
    BASE_DIR + '/templates',
)

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'djcelery',
    'social_auth',
    'captcha',
    'accounts',
    'service',
    'south',
    # 'swampdragon',
    # 'dashboard',
    'django_socketio',
    'django_countries',
    'file_resubmit',
    'django_crontab',
)

MIDDLEWARE_CLASSES = (
    'chillpublic.middleware.ChillPublicMiddleware',
    
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'chillpublic.middleware.SessionIdleTimeout',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'chillpublic.urls'

WSGI_APPLICATION = 'chillpublic.wsgi.application'

SESSION_IDLE_TIMEOUT = 1800

# Database
# https://docs.djangoproject.com/en/1.6/ref/settings/#databases

if getpass.getuser() == 'root':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'chillpublic_new',                      # Or path to database file if using sqlite3.
            'USER': 'postgres',                      # Not used with sqlite3.
            'PASSWORD': 'chillpublic',                  # Not used with sqlite3.
            'HOST': '127.0.0.1',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'chillpublic',                      # Or path to database file if using sqlite3.
            'USER': 'chillpublic',                      # Not used with sqlite3.
    #        'USER': 'postgres',                      # Not used with sqlite3.
            'PASSWORD': 'chillpublic',
    #        'PASSWORD': 'rinjani',                  # Not used with sqlite3.
            'HOST': '127.0.0.1',                      # Set to empty string for localhost. Not used with sqlite3.
            'PORT': '5432',                      # Set to empty string for default. Not used with sqlite3.
        }
    }

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

MEDIA_ROOT = os.path.join(BASE_DIR, 'media') 
MEDIA_URL = '/media/' 

STATIC_URL = '/static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)


AUTHENTICATION_BACKENDS = (
    'social_auth.backends.twitter.TwitterBackend',
    'social_auth.backends.facebook.FacebookBackend',
    'social_auth.backends.google.GoogleOAuthBackend',
    'social_auth.backends.google.GoogleOAuth2Backend',
    'social_auth.backends.google.GoogleBackend',
    'social_auth.backends.yahoo.YahooBackend',
    'social_auth.backends.browserid.BrowserIDBackend',
    'social_auth.backends.contrib.linkedin.LinkedinBackend',
    'social_auth.backends.contrib.disqus.DisqusBackend',
    'social_auth.backends.contrib.livejournal.LiveJournalBackend',
    'social_auth.backends.contrib.orkut.OrkutBackend',
    'social_auth.backends.contrib.foursquare.FoursquareBackend',
    'social_auth.backends.contrib.github.GithubBackend',
    'social_auth.backends.contrib.vk.VKOAuth2Backend',
    'social_auth.backends.contrib.live.LiveBackend',
    'social_auth.backends.contrib.skyrock.SkyrockBackend',
    'social_auth.backends.contrib.yahoo.YahooOAuthBackend',
    'social_auth.backends.contrib.readability.ReadabilityBackend',
    'social_auth.backends.contrib.fedora.FedoraBackend',
    'social_auth.backends.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

#EMAIL SETTINGS
# EMAIL_USE_TLS = True
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'voidnetworklabs@gmail.com'
# EMAIL_HOST_PASSWORD = 'log1000g'
EMAIL_USE_TLS = True
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

#sosial auth key
TWITTER_CONSUMER_KEY         = 'kvDAFkxF62CKkhilqygsK2vGE'
TWITTER_CONSUMER_SECRET      = 'KmEcUMYV6AvMsICwlLf2kDg7fWQvMdrEyHtd9AqAQjh9NqcAj2'
FACEBOOK_APP_ID              = '1527565050791465'
FACEBOOK_API_SECRET          = 'cc1757185ddc9d00b4120aa01ebe54a3'
LINKEDIN_CONSUMER_KEY        = ''
LINKEDIN_CONSUMER_SECRET     = ''
ORKUT_CONSUMER_KEY           = ''
ORKUT_CONSUMER_SECRET        = ''
GOOGLE_CONSUMER_KEY          = ''
GOOGLE_CONSUMER_SECRET       = ''
GOOGLE_OAUTH2_CLIENT_ID      = ''
GOOGLE_OAUTH2_CLIENT_SECRET  = ''
FOURSQUARE_CONSUMER_KEY      = ''
FOURSQUARE_CONSUMER_SECRET   = ''
VK_APP_ID                    = ''
VK_API_SECRET                = ''
LIVE_CLIENT_ID               = ''
LIVE_CLIENT_SECRET           = ''
SKYROCK_CONSUMER_KEY         = ''
SKYROCK_CONSUMER_SECRET      = ''
YAHOO_CONSUMER_KEY           = ''
YAHOO_CONSUMER_SECRET        = ''
READABILITY_CONSUMER_SECRET  = ''

#login url
LOGIN_URL          = '/'
LOGIN_REDIRECT_URL = '/'
LOGIN_ERROR_URL    = '/'

# CAPTCHA SETTINGS
CAPTCHA_FONT_PATH = os.path.join(BASE_DIR, 'courier.ttf')
CAPTCHA_FONT_SIZE = 34

#photo upload dir
PHOTO_UPLOAD = BASE_DIR + '/media/photo/'

ENCRYPTED_FIELDS_KEYDIR = os.path.join(BASE_DIR, 'fieldkeys')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'chillpublic.log'),
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'standard',
        },
        'request_handler': {
                'level':'DEBUG',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': os.path.join(BASE_DIR, 'django_request.log'),
                'maxBytes': 1024*1024*5, # 5 MB
                'backupCount': 5,
                'formatter':'standard',
        },
    },
    'loggers': {

        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['request_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}

CRONJOBS = [
    ('* * * * *', 'crontab.ticket_time'),
]


CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    },
    "file_resubmit": {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        "LOCATION": '/tmp/file_resubmit/'
    },
}

# SWAMP_DRAGON_CONNECTION = ('swampdragon.connections.sockjs_connection.DjangoSubscriberConnection', '/data')


try:
    from local_settings import *
except:
    pass