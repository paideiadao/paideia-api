import asyncio

def run_coroutine_in_sync(coroutine):
   return asyncio.run(coroutine)
