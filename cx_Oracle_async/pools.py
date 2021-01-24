from .context import AbstractContextManager as BaseManager
from .connections import AsyncConnectionWrapper , AsyncConnectionWrapper_context
from ThreadPoolExecutorPlus import ThreadPoolExecutor
from cx_Oracle import Connection , SessionPool
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
        self._occupied = set()

    def acquire(self):
        coro = self._loop.run_in_executor(self._thread_pool , self._acquire)
        return AsyncConnectionWrapper_context(coro)

    def _acquire(self):
        _conn = self._pool.acquire()
        self._occupied.update((_conn , ))
        return AsyncConnectionWrapper(_conn , self._loop , self._thread_pool , self._pool , self)

    def _unoccupied(self , obj: Connection):
        self._occupied.remove(obj)

    async def release(self , conn: Connection):
        return await self._loop.run_in_executor(self._thread_pool , self._pool.release , conn)

    async def drop(self , conn: Connection):
        return await self._loop.run_in_executor(self._thread_pool , self._pool.drop , conn)

    async def close(self , force: bool = False , interrupt: bool = False):
        '''
        WARNING: option `interrupt` will force cancel all running connections before close
        the pool. This may cause fetching thread no response forever in some legacy version
        of oracle database such as 11 or lower.

        Do make sure this option works fine with your working enviornment.
        '''
        while self._occupied:
            _conn = self._occupied.pop()
            if interrupt:
                await self._loop.run_in_executor(self._thread_pool , _conn.cancel)

        return await self._loop.run_in_executor(self._thread_pool , self._pool.close , force)