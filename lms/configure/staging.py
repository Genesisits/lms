from .base import *

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
  'default': {
      'ENGINE': 'django.db.backends.sqlite3',
      'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

AWS_ACCESS_KEY_ID = 'AKIAS2EWQWGCIJTVC6OQ'
AWS_SECRET_ACCESS_KEY = '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'
AWS_STORAGE_BUCKET_NAME = 'lmsfiless3'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_LOCATION = 'static'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static', 'staticfiles'),
]

STATIC_URL = 'https://%s/%s/' % (AWS_S3_CUSTOM_DOMAIN, AWS_LOCATION)
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

DEFAULT_FILE_STORAGE = 'lms.configure.storage_backends.MediaStorage'

# STATICFILES_DIRS = (
#     os.path.join(BASE_DIR, 'static', 'staticfiles'),
# )
#
# MEDIA_ROOT = os.path.join(BASE_DIR, "media")

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.hostinger.in'
# EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'feedback@clusterit.io'
EMAIL_HOST_PASSWORD = 'Cluster@123'
EMAIL_USE_TLS = False
EMAIL_USER = 'feedback@clusterit.io'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            # exact format is not important, this is the minimum information
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'loggers.log',
            'formatter': 'console',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': 'loggers.log',
            'formatter': 'console',
        },
        'debug': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'loggers.log',
            'formatter': 'console',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
