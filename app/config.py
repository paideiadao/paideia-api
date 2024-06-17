import os
import time
import uuid


class dotdict(dict):
    """dot.notation access to dictionary attributes"""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class Stopwatch(object):
    def __init__(self):
        self.start_time = None
        self.stop_time = None

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.stop_time = time.time()

    @property
    def time_elapsed(self):
        return time.time() - self.start_time

    @property
    def total_run_time(self):
        return self.stop_time - self.start_time

    def __enter__(self):
        self.start()
        return self

    def __exit__(self):
        self.stop()


Network = os.getenv("ERGONODE_NETWORK", default="mainnet")
Config = {
    "testnet": dotdict(
        {
            "DEBUG": True,
            "node": os.getenv("ERGONODE_HOST"),
            "connection_string": f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
            "redis_host": os.getenv("REDIS_HOST"),
            "redis_port": os.getenv("REDIS_PORT"),
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "aws_region": os.getenv("AWS_REGION"),
            "s3_bucket": os.getenv("S3_BUCKET"),
            "s3_key": os.getenv("S3_KEY"),
            "jwt_secret": os.getenv("JWT_SECRET_KEY"),
            "ergoauth_seed": os.getenv("ERGOAUTH_SEED"),
            "danaides_api": os.getenv("DANAIDES_API"),
            "paideia_state": os.getenv("PAIDEIA_STATE"),
            "admin_id": uuid.UUID(os.getenv("ADMIN_ID")),
            "notifications_api": os.getenv("NOTIFICATIONS_API"),
            "crux_api": os.getenv("CRUX_API"),
        }
    ),
    "mainnet": dotdict(
        {
            "DEBUG": False,
            "node": os.getenv("ERGONODE_HOST"),
            "connection_string": f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
            "redis_host": os.getenv("REDIS_HOST"),
            "redis_port": os.getenv("REDIS_PORT"),
            "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY"),
            "aws_region": os.getenv("AWS_REGION"),
            "s3_bucket": os.getenv("S3_BUCKET"),
            "s3_key": os.getenv("S3_KEY"),
            "jwt_secret": os.getenv("JWT_SECRET_KEY"),
            "ergoauth_seed": os.getenv("ERGOAUTH_SEED"),
            "danaides_api": os.getenv("DANAIDES_API"),
            "paideia_state": os.getenv("PAIDEIA_STATE"),
            "admin_id": uuid.UUID(os.getenv("ADMIN_ID")),
            "notifications_api": os.getenv("NOTIFICATIONS_API"),
            "crux_api": os.getenv("CRUX_API"),
        }
    ),
}
