from .base import *
import sys

# Setup
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
SECURE_SSL_REDIRECT = False

if 'test' not in sys.argv:
    INSTALLED_APPS += ['debug_toolbar', ]
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware', ]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'jarrett_dev',
        'USER': 'postgres',
        'PASSWORD': 'su',
        'HOST': 'localhost',
        'PORT': '5433',
    }
}

# Static Files
STATIC_URL = '/static/'
STATICFILES_STORAGE = 'compressor.storage.CompressorFileStorage'
COMPRESS_STORAGE = STATICFILES_STORAGE
COMPRESS_URL = STATIC_URL
COMPRESS_ES6_COMPILER_CMD = 'SET NODE_PATH="{paths}" && "{browserify_bin}" "{infile}" -o "{outfile}" -t [ "{node_modules}/babelify" --presets ["{node_modules}/@babel/preset-env"] --global True ]'

# Debug
DEBUG_TOOLBAR_PANELS = [
    'debug_toolbar.panels.versions.VersionsPanel',
    'debug_toolbar.panels.timer.TimerPanel',
    'debug_toolbar.panels.settings.SettingsPanel',
    'debug_toolbar.panels.headers.HeadersPanel',
    'debug_toolbar.panels.request.RequestPanel',
    'debug_toolbar.panels.sql.SQLPanel',
    'debug_toolbar.panels.staticfiles.StaticFilesPanel',
    'debug_toolbar.panels.templates.TemplatesPanel',
    'debug_toolbar.panels.cache.CachePanel',
    'debug_toolbar.panels.signals.SignalsPanel',
    'debug_toolbar.panels.logging.LoggingPanel',
    'debug_toolbar.panels.redirects.RedirectsPanel',
]

# Testing
SELENIUM_IMPLICIT_WAIT_TIME = conf['SELENIUM_IMPLICIT_WAIT_TIME']
