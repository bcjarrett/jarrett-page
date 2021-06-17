from django.conf import settings
from django.core.files.storage import get_storage_class
from storages.backends.s3boto3 import Config, S3Boto3Storage

from jarrett.util_aws import invalidate_static_manifest


class CustomS3BotoStorage(S3Boto3Storage):
    access_key_names = ['S3_ACCESS_KEY']
    secret_key_names = ['S3_SECRET_KEY']
    config = Config(
        connect_timeout=180,
        read_timeout=180,
        retries={
            'max_attempts': 10,
        },
    )


class StaticStorage(CustomS3BotoStorage):
    location = settings.STATICFILES_LOCATION
    default_acl = 'public-read'
    AWS_IS_GZIPPED = True
    bucket_name = settings.S3_STATIC_FILES_BUCKET_NAME
    custom_domain = settings.S3_STATIC_FILES_DOMAIN_NAME


class PrivateStorage(CustomS3BotoStorage):
    bucket_name = settings.S3_PRIVATE_FILES_BUCKET_NAME
    custom_domain = settings.S3_PRIVATE_FILES_DOMAIN_NAME


class CachedStaticStorage(StaticStorage):
    """
    S3 storage backend that saves the files locally, too.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.local_storage = get_storage_class(
            "compressor.storage.CompressorFileStorage")()

    def save(self, name, content, max_length=None):
        self.local_storage._save(name, content)
        super().save(name, self.local_storage._open(name), max_length=max_length)
        if name == f'{settings.COMPRESS_OUTPUT_DIR}\manifest.json':
            invalidate_static_manifest(name)
        return name
