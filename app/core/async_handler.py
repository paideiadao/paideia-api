import asyncio
import time
import threading


def run_coroutine_in_sync(coroutine):
    return asyncio.run(coroutine)


class AsyncTaskRunner():
    TIMEOUT = 300  # run crons every 5 mins

    def __init__(self):
        self.tasks = []

    @staticmethod
    def wrapped_func(func):
        while True:
            try:
                func()
            except Exception as e:
                print(str(e))
            time.sleep(AsyncTaskRunner.TIMEOUT)

    def register(self, func):
        self.tasks.append(func)

    def start(self):
        threads = []
        for task in self.tasks:
            threads.append(threading.Thread(
                target=AsyncTaskRunner.wrapped_func, args=(task,)))
        for thread in threads:
            thread.start()
