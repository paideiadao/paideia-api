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

POSTGRES_PORT = os.getenv('POSTGRES_PORT')
POSTGRES_USER = os.getenv('POSTGRES_USER')

Network = os.getenv('ERGONODE_NETWORK', default='mainnet')
Config = {
    'testnet': dotdict({
        'node'              : os.getenv('ERGONODE_HOST'),
        'connectionString'  : f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
        'DEBUG'             : True,
    }),
    'mainnet': dotdict({
        'node'              : os.getenv('ERGONODE_HOST'),
        'connectionString'  : f"postgresql+asyncpg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNM')}",
        'DEBUG'             : True,
    })
}
