from pathlib import Path
from dotenv import load_dotenv
import os
from corsheaders.defaults import default_headers

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Define the environment: 'development' or 'production'
ENVIRONMENT = 'development'  # Change this to 'production' for production settings

# Load the corresponding .env file
env_file = '.env.development' if ENVIRONMENT == 'development' else '.env.production'
load_dotenv(dotenv_path=env_file)

# SECURITY WARNING: keep the secret key used in production secret!
URL_HASH_SECRET_KEY = os.getenv('URL_HASH_SECRET_KEY', 'your-default-secret-key')

#Lusha Settings
LUSHA_API_KEY = os.getenv('LUSHA_API_KEY')
LUSHA_BASE_URL = os.getenv('LUSHA_BASE_URL')

# WAAPI API Key
WAAPI_API_KEY = os.getenv('WAAPI_API_KEY')
WAAPI_BASE_URL = os.getenv('WAAPI_BASE_URL')
WAAPI_INSTANCE_ID = os.getenv('WAAPI_INSTANCE_ID')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False')
SECRET_KEY = os.getenv('SECRET_KEY', 'your-default-secret-key')
ALLOWED_HOSTS = ['*']
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:8100')  # Replace this with your Vue app's URL

# Strict CORS configuration
# In Django settings.py
CORS_ALLOWED_ORIGINS = ['http://localhost', 'http://localhost:80']
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = list(default_headers) + [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


SITE_ID = 1

USE_TZ = True
TIME_ZONE = 'Africa/Johannesburg'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',  # You can remove this if you don't need sessions at all
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps
    'users',
    'utilities',
    'messaging',
    'datahub',
    'engage',

    # Third party apps
    'rest_framework',
    'drf_yasg',
    'corsheaders',
    'rest_framework.authtoken',  # Necessary for Token Authentication
    'dj_rest_auth',  # Provides REST API endpoints for authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'dj_rest_auth.registration',
    'django_extensions',
    'django_celery_beat',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',  # Keep this for Django admin
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'engage.middleware.SecureURLMiddleware'
]
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

ROOT_URLCONF = 'core.urls'

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
CORS_ALLOW_ALL_ORIGINS = True

WSGI_APPLICATION = 'core.wsgi.application'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("POSTGRES_DB", "postgres"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "postgres"),
        "HOST": os.environ.get("POSTGRES_HOST", "db"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432")
    }
}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Johannesburg'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,  # Items per page
}

# Disable CSRF if you're not using session-based authentication
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# Allauth settings
HEADLESS_ONLY = True
ACCOUNT_AUTHENTICATION_METHOD = 'username_email'
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # Require email verification
ACCOUNT_EMAIL_REQUIRED = True  # Require email field
ACCOUNT_CONFIRM_EMAIL_ON_GET = True  # Auto confirm when the user clicks the link
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_UNIQUE_EMAIL = True
REST_AUTH_REGISTER_SERIALIZER = 'users.serializers.CustomRegisterSerializer'
ACCOUNT_SIGNUP_REDIRECT_URL = None  # Prevent redirection
ACCOUNT_SIGNUP_FORM_CLASS = None  # Disable the default Allauth form rendering
ACCOUNT_ADAPTER = "utilities.adapters.CustomAccountAdapter"
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": f"{FRONTEND_URL}/verify-email/{{key}}",
    "account_reset_password": f"{FRONTEND_URL}/password/reset",
    "account_reset_password_from_key": f"{FRONTEND_URL}/password/reset/key/{{key}}",
    "account_signup": f"{FRONTEND_URL}/signup",
    "account_login": f"{FRONTEND_URL}/login",  # Ensure login is mapped
}


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # For testing, logs emails to the console
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Use this for actual email sending
EMAIL_HOST = 'smtp.your-email-provider.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-email-password'
DEFAULT_FROM_EMAIL = 'your-email@example.com'

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')

SITE_NAME = 'Boilerplate'  # Name of your site for the email subject

# Redis settings
REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')  # Use 'redis' container hostname
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')
REDIS_DB = os.environ.get('REDIS_DB', '0')

# Celery settings
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')  # Redis as message broker
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')  # Redis to store task results
CELERY_ACCEPT_CONTENT = ['json']  # Celery will accept content in JSON
CELERY_TASK_SERIALIZER = 'json'  # Serializer format for tasks
CELERY_TIMEZONE = TIME_ZONE

# Celery Beat Settings
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers.DatabaseScheduler'


# Synthesia API Key
SYNTHESIA_API_KEY = os.getenv('SYNTHESIA_API_KEY')


# Business Hours
OPENING_HOUR = "08:00"
CLOSING_HOUR = "17:00"

# URL Encryption Key
# Either generate a key or use an environment variable
URL_ENCRYPTION_KEY = os.environ.get('URL_ENCRYPTION_KEY')