from .base import *
from urllib.parse import urlparse, uses_netloc

# Setup
DEBUG = False
ALLOWED_HOSTS = ['jarrett.page', ]
SECURE_SSL_REDIRECT = True

# Database
uses_netloc.append("postgres")
url = urlparse(conf['DATABASE_URL'])
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': url.path[1:],
        'USER': url.username,
        'PASSWORD': url.password,
        'HOST': url.hostname,
        'PORT': url.port,
    }
}

# Static files
CF_STATIC_DISTRO_ID = conf['CF_STATIC_DISTRO_ID']
STATICFILES_STORAGE = 'jarrett.storage_backends.CachedStaticStorage'
STATIC_URL = conf['STATIC_URL']

# Compressor
COMPRESS_STORAGE = STATICFILES_STORAGE
COMPRESS_URL = STATIC_URL
COMPRESS_ES6_COMPILER_CMD = 'SET NODE_PATH="{paths}" && "{browserify_bin}" "{infile}" -o "{outfile}" -t [ "{node_modules}/babelify" --presets ["{node_modules}/@babel/preset-env"] --global True ]'
