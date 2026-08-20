import os
import sys
from pathlib import Path
from datetime import timedelta
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-saec-cafe-c++-cafe-secret-key-2026-production-ready-key')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')

# ALLOWED_HOSTS: Permissive for Railway & Cloud deployment
raw_allowed_hosts = os.getenv('ALLOWED_HOSTS', '*')
if raw_allowed_hosts.strip() == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [host.strip() for host in raw_allowed_hosts.split(',') if host.strip()]
    if '*' not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.extend(['.railway.app', '.up.railway.app', 'localhost', '127.0.0.1', 'web-production-85e59.up.railway.app'])

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Custom SAEC Cafe Apps
    'apps.accounts',
    'apps.business_days',
    'apps.products',
    'apps.inventory',
    'apps.orders',
    'apps.payments',
    'apps.payment_support',
    'apps.contact_orders',
    'apps.analytics',
    'apps.notifications',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
]

try:
    import whitenoise  # noqa: F401
    MIDDLEWARE.append('whitenoise.middleware.WhiteNoiseMiddleware')
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
except ImportError:
    pass

MIDDLEWARE.extend([
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
])


ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database Configuration (Railway DATABASE_URL / Local PostgreSQL / SQLite fallback)
database_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_PUBLIC_URL') or os.getenv('POSTGRES_URL')
USE_POSTGRES = os.getenv('USE_POSTGRES', 'True').lower() in ('true', '1', 't')

import re
import urllib.parse

def parse_db_url(url_str: str) -> dict:
    """Crash-proof helper to parse any database URL string into Django DATABASES settings."""
    if not url_str or not isinstance(url_str, str):
        return {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}
    
    url_clean = url_str.strip().strip("'\"")
    
    # 1. Try standard dj_database_url
    try:
        import dj_database_url
        res = dj_database_url.parse(url_clean, conn_max_age=600, conn_health_checks=True)
        if res and res.get('ENGINE'):
            return res
    except Exception:
        pass

    # 2. Resilient manual parser for URLs with unquoted special characters
    try:
        m = re.match(r'^(?:postgres|postgresql|sqlite|sqlite3)://(.*)$', url_clean)
        if m:
            rest = m.group(1)
            if '/' in rest:
                auth_host, dbname = rest.rsplit('/', 1)
                dbname = dbname.split('?')[0]
                if '@' in auth_host:
                    auth_part, host_port = auth_host.rsplit('@', 1)
                    if ':' in auth_part:
                        user, password = auth_part.split(':', 1)
                    else:
                        user, password = auth_part, ''
                else:
                    user, password = '', ''
                    host_port = auth_host
                
                if ':' in host_port:
                    host, port = host_port.split(':', 1)
                else:
                    host, port = host_port, '5432'
                
                return {
                    'ENGINE': 'django.db.backends.postgresql',
                    'NAME': unquote(dbname) if dbname else 'railway',
                    'USER': unquote(user or 'postgres'),
                    'PASSWORD': unquote(password or ''),
                    'HOST': host or '127.0.0.1',
                    'PORT': str(port or 5432),
                    'CONN_MAX_AGE': 600,
                    'CONN_HEALTH_CHECKS': True,
                }
    except Exception:
        pass

    # 3. Fallback to standard urlparse
    try:
        parsed = urlparse(url_clean)
        if parsed.scheme in ('sqlite', 'sqlite3'):
            return {'ENGINE': 'django.db.backends.sqlite3', 'NAME': parsed.path.lstrip('/') or (BASE_DIR / 'db.sqlite3')}
        if parsed.hostname:
            return {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': unquote(parsed.path.lstrip('/')).split('?')[0] or 'railway',
                'USER': unquote(parsed.username or 'postgres'),
                'PASSWORD': unquote(parsed.password or ''),
                'HOST': parsed.hostname,
                'PORT': str(parsed.port or 5432),
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
            }
    except Exception:
        pass

    # 4. Safe SQLite Fallback
    return {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

if database_url:
    DATABASES = {
        'default': parse_db_url(database_url)
    }
elif os.getenv('DB_HOST') and os.getenv('DB_HOST') not in ('127.0.0.1', 'localhost'):
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME', 'saec_cafe'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
elif USE_POSTGRES and os.getenv('DB_HOST') == '127.0.0.1':
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME', 'saec_cafe'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
            'HOST': '127.0.0.1',
            'PORT': os.getenv('DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6},
    },
]

# Internationalization & Business Timezone
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static & Media files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# Simple JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Configuration
raw_cors = os.getenv('CORS_ALLOWED_ORIGINS', '')
if raw_cors.strip():
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in raw_cors.split(',') if origin.strip()]
    CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'False').lower() in ('true', '1', 't')
else:
    CORS_ALLOWED_ORIGINS = [
        'https://cafe-management-frontend-kappa.vercel.app',
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ]
    CORS_ALLOW_ALL_ORIGINS = os.getenv('CORS_ALLOW_ALL_ORIGINS', 'False').lower() in ('true', '1', 't')

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]

CORS_ALLOW_CREDENTIALS = True

# CSRF Trusted Origins
raw_csrf = os.getenv('CSRF_TRUSTED_ORIGINS', '')
if raw_csrf.strip():
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in raw_csrf.split(',') if origin.strip()]
else:
    CSRF_TRUSTED_ORIGINS = [
        'https://cafe-management-frontend-kappa.vercel.app',
        'https://web-production-85e59.up.railway.app',
        'https://*.vercel.app',
        'https://*.railway.app',
        'https://*.up.railway.app',
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Safe Production Logging (No secrets or credentials exposed)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'simple': {
            'format': '%(levelname)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
            'stream': sys.stdout,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


