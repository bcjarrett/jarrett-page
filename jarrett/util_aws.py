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

from .util import thread_task


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


def s3_resource():
    return boto3.resource(
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


def s3_create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object
    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3',
                             aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, )
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None
    # The response contains the presigned URL
    return response


def s3_delete_object(bucket_name, object_name):
    s3_client = boto3.client('s3',
                             aws_access_key_id=settings.S3_ACCESS_KEY,
                             aws_secret_access_key=settings.S3_SECRET_KEY, )
    try:
        response = s3_client.delete_object(
            Bucket=bucket_name,
            Key=object_name,
        )
    except ClientError as e:
        logging.error(e)
        return None
    return response


def update_s3_object_storage_class(s3_object_summary, storage_class: str) -> bool:
    """
    Update storage class for s3.ObjectSummary

    Available storage classes:
    [STANDARD, REDUCED_REDUNDANCY, STANDARD_IA, ONEZONE_IA, GLACIER, DEEP_ARCHIVE]

    :param s3_object_summary: Current s3.ObjectSummary
    :param storage_class: desired storage class, chose from list above
    :return: True if changed, false if ignored
    """
    storage_classes = ['STANDARD', 'REDUCED_REDUNDANCY', 'STANDARD_IA', 'ONEZONE_IA', 'GLACIER', 'DEEP_ARCHIVE']
    minimum_ia_size = 131072  # bytes
    current_storage_class = s3_object_summary.storage_class

    if storage_class not in storage_classes:
        raise TypeError(f'{storage_class} is not a valid storage_class.\n'
                        f'Options are {storage_classes}')

    if storage_class == current_storage_class:
        return False

    if current_storage_class in ['GLACIER', 'DEEP_ARCHIVE']:
        raise TypeError(f'FAILED TO UPDATE {s3_object_summary}\n:::'
                        f'Glacier and Deep Freeze objects must be restored to change their storage class')

    if storage_class in ['STANDARD_IA', 'ONEZONE_IA']:
        # Check for min size or get charged a lot for really small files
        if s3_object_summary.size < minimum_ia_size:
            return False

    # If not glacier and not too small update the storage class by copying to itself
    s3_object = s3_object_summary.Object()
    s3_object.copy(
        {'Bucket': s3_object.bucket_name, 'Key': s3_object.key},
        ExtraArgs={
            'StorageClass': storage_class,
        }
    )
    return True


def update_s3_folder_storage_class(bucket_name, folder_prefix, storage_class):
    client = s3_resource()
    bucket = client.Bucket(bucket_name)
    s3_object_summaries = list(bucket.objects.filter(Prefix=folder_prefix))
    thread_task(update_s3_object_storage_class, s3_object_summaries, storage_class=storage_class)


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
