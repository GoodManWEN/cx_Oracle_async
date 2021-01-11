from .context import AbstractContextManager as BaseManager
from .connections import AsyncConnectionWrapper , AsyncConnectionWrapper_context
from ThreadPoolExecutorPlus import ThreadPoolExecutor
from cx_Oracle import SessionPool
from types import CoroutineType
import asyncio
import platform
import os
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asyncio.windows_events import ProactorEventLoop

pltfm = platform.system()
if pltfm == 'Windows':
    DEFAULT_MAXIMUM_WORKER_NUM = (os.cpu_count() or 1) * 16
    DEFAULT_MAXIMUM_WORKER_TIMES = 2
elif pltfm == 'Linux' or pltfm == 'Darwin':
    DEFAULT_MAXIMUM_WORKER_NUM = (os.cpu_count() or 1) * 32
    DEFAULT_MAXIMUM_WORKER_TIMES = 3


class AsyncPoolWrapper_context(BaseManager):

    def __init__(self , coro : CoroutineType):
        super().__init__(coro)

    async def __aexit__(self, exc_type, exc, tb):
        await self._obj.close()
        self._obj = None


class AsyncPoolWrapper:
    
    def __init__(self , pool : SessionPool, loop : 'ProactorEventLoop' = None):
        if loop == None:
            loop = asyncio.get_running_loop()
        self._thread_pool = ThreadPoolExecutor(max_workers = max(DEFAULT_MAXIMUM_WORKER_NUM , pool.max << DEFAULT_MAXIMUM_WORKER_TIMES)) 
        self._thread_pool.set_daemon_opts(min_workers = max(4 , pool.min << 1))
        self._loop = loop 
        self._pool = pool 

    def acquire(self):
        coro = self._loop.run_in_executor(self._thread_pool , self._acquire)
        return AsyncConnectionWrapper_context(coro)

    def _acquire(self):
        return AsyncConnectionWrapper(self._pool.acquire() , self._loop , self._thread_pool , self._pool)

    async def close(self):
        return await self._loop.run_in_executor(self._thread_pool , self._pool.close)