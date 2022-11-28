import boto3
from config import Config, Network

CFG = Config[Network]

S3 = boto3.client(
    "s3",
    aws_access_key_id=CFG.aws_access_key_id,
    aws_secret_access_key=CFG.aws_secret_access_key,
)
