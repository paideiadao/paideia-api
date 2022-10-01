import os
import boto3
from botocore.client import Config as botoConfig
from config import Config, Network

CFG = Config[Network]

S3 = boto3.resource(
    's3',
    aws_access_key_id=CFG.aws_access_key_id,
    aws_secret_access_key=CFG.aws_secret_access_key,
    config=botoConfig(signature_version='s3v4')
)
