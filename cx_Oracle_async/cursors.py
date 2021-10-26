from .context import AbstractContextManager as BaseManager
from ThreadPoolExecutorPlus import ThreadPoolExecutor
from types import CoroutineType
from cx_Oracle import Cursor
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asyncio.windows_events import ProactorEventLoop


class AsyncCursorWrapper_context(BaseManager):

    def __init__(self , coro : CoroutineType):
        super().__init__(coro)


class AsyncCursorWrapper:

    def __init__(self , cursor : Cursor, loop : 'ProactorEventLoop' , thread_pool : ThreadPoolExecutor):
        self._cursor = cursor
        self._loop = loop
        self._thread_pool = thread_pool

    async def execute(self , sql , *args , **kwargs):
        if kwargs:
            return await self._loop.run_in_executor(
                self._thread_pool , 
                lambda : self._cursor.execute(sql , *args , **kwargs)
            )
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.execute , sql , *args , **kwargs)

    async def executemany(self , sql , *args , **kwargs):
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.executemany , sql , *args , **kwargs)

    async def fetchone(self):
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.fetchone)

    async def fetchall(self):
        # block mainly happens when fetch triggered.
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.fetchall)

    async def var(self, args):
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.var, args)
    
    async def callproc(self, *args , **kwargs):
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.callproc, *args , **kwargs)
