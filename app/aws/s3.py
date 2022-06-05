import os
import boto3
from botocore.client import Config
from config import Config, Network

CFG = Config[Network]

S3 = boto3.resource(
    's3',
    aws_access_key_id=CFG.awsAccessKeyId,
    aws_secret_access_key=CFG.awsSecretAccessKey,
    config=Config(signature_version='s3v4')
)
