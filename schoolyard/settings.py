import os
from pathlib import Path
from urllib.parse import urlparse

from cryptography.hazmat.primitives.serialization import load_ssh_private_key, load_ssh_public_key

SCHOOLYARD_VERSION = '0.15.1'
SCHOOLYARD_ENVIRONMENT = os.environ ['SCHOOLYARD_ENV']

BASE_DIR = Path (__file__).resolve ().parent.parent

SECRET_KEY = os.environ ['SECRET_KEY']

DEBUG = (os.environ ['DEBUG'].lower () == 'true')

ALLOWED_HOSTS = os.environ ['ALLOWED_HOSTS'].split (',')

INSTALLED_APPS = [
    'landing',
    'api.doc',
    'api.users',
    'api.teams',
    'api.events',
    'api.rest_auth',
    'api.challenges',
    'api.scoring',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'phonenumber_field',
    'drf_spectacular' ]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

ROOT_URLCONF = 'schoolyard.urls'

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
                'django.contrib.messages.context_processors.messages' ] } } ]

WSGI_APPLICATION = 'schoolyard.wsgi.application'

db_url = urlparse (os.environ ['DATABASE_URL'])

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': db_url.path [1:],
        'USER': db_url.username,
        'PASSWORD': db_url.password,
        'HOST': db_url.hostname,
        'PORT': db_url.port } }

AUTH_PASSWORD_VALIDATORS = [
    { 'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator' },
    { 'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator' } ]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'schoolyard/static'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

TEST_RUNNER = 'schoolyard.tests.SchoolyardTestRunner'

REST_FRAMEWORK = {
    'DEFAULT_PARSER_CLASSES': ['rest_framework.parsers.JSONParser'],
    'DEFAULT_AUTHENTICATION_CLASSES': [ 'api.rest_auth.authentication.APIKeyAuthentication' ],
    'DEFAULT_PERMISSION_CLASSES': [ 'api.rest_auth.permissions.AnonymousAPIUserAccess' ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'NON_FIELD_ERRORS_KEY': 'detail',
    'COERCE_DECIMAL_TO_STRING': False }

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_true': { '()': 'django.utils.log.RequireDebugTrue' },
        'require_sql_query_log_path': { '()': 'schoolyard.log.RequireSQLQueryLogPath' } },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.FileHandler',
            'filename': os.environ.get ('SQL_QUERY_LOG_PATH', '/dev/null') } },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['file'] } } }

API_AUTH_ANONYMOUS_KEY = os.environ ['ANONYMOUS_API_KEY']
API_AUTH_OTP_LENGTH = 6
API_AUTH_JWT_VERSION = os.environ ['JWT_VERSION']
API_AUTH_JWT_PRIVATE_KEY = load_ssh_private_key (os.environ ['JWT_PRIVATE_KEY'].encode ('latin1').decode ('unicode_escape').encode ('latin1'), password=b'')
API_AUTH_JWT_PUBLIC_KEY = load_ssh_public_key (os.environb [b'JWT_PUBLIC_KEY'])
API_AUTH_JWT_ALGORITHM = 'RS256'
API_AUTH_ACCESS_TOKEN_LIFETIME_S = int (os.environ ['JWT_ACCESS_TOKEN_LIFETIME_S'])
API_AUTH_REFRESH_TOKEN_LIFETIME_S = int (os.environ ['JWT_REFRESH_TOKEN_LIFETIME_S'])
API_AUTH_FERNET_KEY = os.environb [b'FERNET_KEY']

SPECTACULAR_SETTINGS = {
    'TITLE': 'Schoolyard API',
    'DESCRIPTION': 'API Backend to support Schoolyard apps.',
    'VERSION': SCHOOLYARD_VERSION,
    'EXTERNAL_DOCS': {'description': 'ChangeLog', 'url': STATIC_URL + 'doc/ChangeLog.txt'},
    'PREPROCESSING_HOOKS': ['api.doc.urls.openapi_preprocess_exclude_schema'] }

# services

TWILIO = {
    'PHONE_NUMBER': os.environ ['TWILIO_PHONE_NUMBER'],
    'ACCOUNT_SID': os.environ ['TWILIO_ACCOUNT_SID'],
    'AUTH_TOKEN': os.environ ['TWILIO_AUTH_TOKEN'],
    'VERIFY_SERVICE_ID': os.environ ['TWILIO_VERIFY_SERVICE_ID'] }

SENDBIRD = {
    "API_URL": os.environ ["SENDBIRD_API_URL"],
    "TOKEN": os.environ ["SENDBIRD_TOKEN"],
    "API_VERSION": "v3" }

# constants

DAY_S = 24 * 60 * 60
