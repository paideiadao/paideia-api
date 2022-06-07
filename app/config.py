import os
import time


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


Network = os.getenv('ERGONODE_NETWORK', default='mainnet')
Config = {
    'testnet': dotdict({
        'DEBUG': True,
        'node': os.getenv('ERGONODE_HOST'),
        'connectionString': f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
        'redisHost': os.getenv('REDIS_HOST'),
        'redisPort': os.getenv('REDIS_PORT'),
        'awsAccessKeyId': os.getenv("AWS_ACCESS_KEY_ID"),
        'awsSecretAccessKey': os.getenv("AWS_SECRET_ACCESS_KEY"),
        'awsRegion': os.getenv("AWS_REGION"),
        's3Bucket': os.getenv("S3_BUCKET"),
        's3Key': os.getenv("S3_KEY"),
        'jwtSecret': os.getenv("JWT_SECRET_KEY"),
    }),
    'mainnet': dotdict({
        'DEBUG': False,
        'node': os.getenv('ERGONODE_HOST'),
        'connectionString': f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
        'redisHost': os.getenv('REDIS_HOST'),
        'redisPort': os.getenv('REDIS_PORT'),
        'awsAccessKeyId': os.getenv("AWS_ACCESS_KEY_ID"),
        'awsSecretAccessKey': os.getenv("AWS_SECRET_ACCESS_KEY"),
        'awsRegion': os.getenv("AWS_REGION"),
        's3Bucket': os.getenv("S3_BUCKET"),
        's3Key': os.getenv("S3_KEY"),
        'jwtSecret': os.getenv("JWT_SECRET_KEY"),
    })
}
