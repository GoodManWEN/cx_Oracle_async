from .context import AbstractContextManager as BaseManager
from .cursors import AsyncCursorWrapper , AsyncCursorWrapper_context
from .AQ import AsyncQueueWrapper
from cx_Oracle import Connection , SessionPool
from ThreadPoolExecutorPlus import ThreadPoolExecutor
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asyncio.windows_events import ProactorEventLoop

class AsyncConnectionWrapper_context(BaseManager):

    def __init__(self , coro):
        super().__init__(coro)

    async def __aexit__(self, exc_type, exc, tb):
        await self._obj.release()
        self._obj = None


class AsyncConnectionWrapper:

    def __init__(self , conn: Connection, loop: 'ProactorEventLoop', thread_pool: ThreadPoolExecutor, pool: SessionPool):
        self._conn = conn  
        self._loop = loop
        self._pool = pool
        self._thread_pool = thread_pool

    def cursor(self):
        coro = self._loop.run_in_executor(self._thread_pool , self._cursor)
        return AsyncCursorWrapper_context(coro)

    def _cursor(self):
        return AsyncCursorWrapper(self._conn.cursor() , self._loop , self._thread_pool)

    def msgproperties(self , *args , **kwargs):
        return self._conn.msgproperties(*args , **kwargs)

    @property
    def encoding(self):
        return self._conn.encoding

    async def queue(self , *args , **kwargs):
        return AsyncQueueWrapper(self._conn.queue(*args , **kwargs) , self._loop , self._thread_pool , self)

    async def gettype(self , *args , **kwargs):
        '''
        Uses the original cx_Oracle object without wrapper
        '''
        return await self._loop.run_in_executor(self._thread_pool , self._conn.gettype , *args , **kwargs)

    async def commit(self):
        await self._loop.run_in_executor(self._thread_pool , self._conn.commit)

    async def release(self):
        return await self._loop.run_in_executor(self._thread_pool , self._pool.release , self._conn)