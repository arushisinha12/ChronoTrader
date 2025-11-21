"""
Django settings for gamename project.
"""
import os
from pathlib import Path

from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parent.parent

# ----------------------------------------------------------------------
# 🔑 SECURITY CONFIGURATION (CRUCIAL FOR PRODUCTION)
# ----------------------------------------------------------------------

SECRET_KEY = os.environ.get('SECRET_KEY', get_random_secret_key())
DEBUG = False

ALLOWED_HOSTS = ['chronotrader.pythonanywhere.com',
                 'progchamp.vercel.app',
                 '*',]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'game_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # --- CRITICAL CHANGE: CSRF MIDDLEWARE REMOVED ---
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # ------------------------------------------------
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    #'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gamename.urls'

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

WSGI_APPLICATION = 'gamename.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ----------------------------------------------------------------------
# 🖼️ STATIC FILES CONFIGURATION 
# ----------------------------------------------------------------------

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = []


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Cookie Settings (Mandatory for Iframe/Third-Party Context) ---
# CRITICAL: Must be the string 'None' (case-sensitive) for cross-site cookies.
SESSION_COOKIE_SAMESITE = 'None' 
CSRF_COOKIE_SAMESITE = 'None'

SESSION_COOKIE_SECURE = True # Requires HTTPS to work.
CSRF_COOKIE_SECURE = True

CSRF_TRUSTED_ORIGINS = [
    "https://chronotrader.pythonanywhere.com",
    "http://chronotrader.pythonanywhere.com",
    "https://progchamp.vercel.app", 
    "https://*.vercel.app",
]