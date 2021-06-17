"""
For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

from pathlib import Path

from jarrett.config import Config

conf = Config()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = conf['DJANGO_SECRET_KEY']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',
    'compressor',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'ratelimitbackend.middleware.RateLimitMiddleware'
]

ROOT_URLCONF = 'jarrett.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'jarrett.wsgi.application'

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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
]

AUTHENTICATION_BACKENDS = (
    'ratelimitbackend.backends.RateLimitModelBackend',
)

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = (
    BASE_DIR / 'static',
    BASE_DIR / 'node_modules' / 'bootstrap' / 'dist',
    BASE_DIR / 'node_modules' / '@fortawesome',
    BASE_DIR / 'node_modules' / 'jquery' / 'dist',
)

COMPRESS_ROOT = STATIC_ROOT
COMPRESS_OUTPUT_DIR = 'source'
COMPRESS_OFFLINE = True
COMPRESS_FILTERS = {
    'css': [
        'compressor.filters.css_default.CssAbsoluteFilter',
        'compressor.filters.cssmin.CSSMinFilter',
        'compressor.filters.template.TemplateFilter'
    ],
    'js': [
        'compressor.filters.jsmin.JSMinFilter',
    ],
}
COMPRESS_PRECOMPILERS = (
    ('module', 'jarrett.compress_toolchain.precompilers.ES6Compiler'),
    ('css', 'jarrett.compress_toolchain.precompilers.SCSSCompiler'),
)
S3_STATIC_FILES_DOMAIN_NAME = conf['S3_STATIC_FILES_DOMAIN_NAME']
S3_STATIC_FILES_BUCKET_NAME = conf['S3_STATIC_FILES_BUCKET_NAME']


# AWS Credentials
CF_ACCESS_KEY = conf['CF_ACCESS_KEY']               # Programmatic access to CF account
CF_SECRET_KEY = conf['CF_SECRET_KEY']
CF_KEYPAIR_KEY = conf['CF_KEYPAIR_KEY']             # Used to generate pre-signed urls
CF_KEYPAIR_PEM = conf['CF_KEYPAIR_PEM']
CF_STATIC_DISTRO_ID = conf['CF_STATIC_DISTRO_ID']   # Distro ID used when invalidating manifest
S3_ACCESS_KEY = conf['S3_ACCESS_KEY']               # Programmatic access to S3 account
S3_SECRET_KEY = conf['S3_SECRET_KEY']


COMPRESS_ENABLED = True

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
