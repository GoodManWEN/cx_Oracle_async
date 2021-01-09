from .context import AbstractContextManager as BaseManager


class AsyncCursorWrapper_context(BaseManager):

    def __init__(self , coro):
        super().__init__(coro)


class AsyncCursorWrapper:

    def __init__(self , cursor , loop , thread_pool):
        self._cursor = cursor
        self._loop = loop
        self._thread_pool = thread_pool

    async def execute(self , sql , *args , **kwargs):
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