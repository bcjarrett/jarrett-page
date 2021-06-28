import datetime
import logging

import boto3
from botocore.exceptions import ClientError
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from django.conf import settings
from django.db import models
from django.db.models.fields.files import FieldFile, FileField, ImageField, ImageFile
from django.test import TestCase


class CFFieldFile(FieldFile):
    @property
    def cf_url(self):
        return signed_cf_url(self.storage.bucket.name, self.name)


class CFFileField(models.FileField):
    attr_class = CFFieldFile
    description = "CloudFront File"


class CFImageField(ImageFile):
    @property
    def cf_url(self):
        return signed_cf_url(self.storage.bucket.name, self.name)


class CFImageFileField(models.FileField):
    attr_class = CFFieldFile
    description = "CloudFront Image File"


def s3_client():
    return boto3.client(
        's3',
        aws_secret_access_key=settings.S3_SECRET_KEY,
        aws_access_key_id=settings.S3_ACCESS_KEY
    )


def cf_client():
    return boto3.client(
        'cloudfront',
        aws_secret_access_key=settings.CF_SECRET_KEY,
        aws_access_key_id=settings.CF_ACCESS_KEY
    )


class S3CleanupTestCase(TestCase):
    """
    Base test class that will scan the TestCase instance for related
    models with Files and try and delete anything from S3

    Could potentially delete real data if data provided to filefields
    is not dummy data
    """

    @staticmethod
    def delete_s3_file_fields(dj_model):
        model_fields = dj_model._meta.fields
        for field in model_fields:
            if type(field) in [FileField, ImageField, CFFileField, CFImageFileField]:
                if getattr(dj_model, field.name):
                    print(f'Deleting from S3 {field.storage.bucket.name}/'
                          f'{field.storage.location}/'
                          f'{getattr(dj_model, field.name).name}')
                    s3 = s3_client()
                    s3.delete_object(Bucket=field.storage.bucket.name,
                                     Key=f'{field.storage.location}/'
                                         f'{getattr(dj_model, field.name).name}')
        return dj_model

    @staticmethod
    def scan_object_for_django_models(obj_list):
        dj_models = set()
        new_models = set()
        for obj in obj_list:
            if obj:
                for val in obj.__dict__:
                    if isinstance(getattr(obj, val), models.Model):
                        dj_models.add(getattr(obj, val))
        if dj_models:
            new_models = S3CleanupTestCase.scan_object_for_django_models(dj_models)
        return dj_models.union(new_models)

    def tearDown(self):
        related_dj_models = self.scan_object_for_django_models([self])
        for model in related_dj_models:
            self.delete_s3_file_fields(model)
        super().tearDown()


def rsa_signer(message):
    private_key = serialization.load_pem_private_key(
        settings.CF_KEYPAIR_PEM.encode(),
        password=None,
        backend=default_backend()
    )
    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())


def signed_cf_url(bucket, key, expires_in_days=7):
    policy = f"""{{
       "Statement": [
          {{
             "Resource":"https://{bucket}/{key}",
             "Condition":{{
                "DateLessThan":{{"AWS:EpochTime":
                {int((datetime.datetime.today() + datetime.timedelta(days=expires_in_days)).timestamp())}}}
             }}
          }}
       ]
    }}"""
    cloudfront_signer = CloudFrontSigner(settings.CF_KEYPAIR_ID, rsa_signer)
    return cloudfront_signer.generate_presigned_url(f'https://{bucket}/{key}', policy=policy)


def cf_key(bucket, key, expires_in_days=7):
    policy = f"""{{
       "Statement": [
          {{
             "Resource":"https://{bucket}/{key}",
             "Condition":{{
                "DateLessThan":{{"AWS:EpochTime":
                {int((datetime.datetime.today() + datetime.timedelta(days=expires_in_days)).timestamp())}}}
             }}
          }}
       ]
    }}"""
    cloudfront_signer = CloudFrontSigner(settings.CLOUDFRONT_KEY, rsa_signer)
    url = cloudfront_signer.generate_presigned_url(f'https://{bucket}/{key}', policy=policy)
    return f'{url.split("?")[-1]}'


def invalidate_static_manifest(name):
    name = name.replace('\\', '/')
    try:
        return cf_client().create_invalidation(
            DistributionId=settings.CF_STATIC_DISTRO_ID,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': [
                        f'/{settings.STATICFILES_LOCATION}/{name}',
                    ]
                },
                'CallerReference': 'jarrett.page'
            }
        )
    except Exception as e:
        print(f'Invalidation Failed::{name}')
        return None
