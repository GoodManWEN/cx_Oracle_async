from sqlalchemy.engine import Engine, Connection
from sqlalchemy import text
from typing import Optional, Any
from collections.abc import Iterable
from ThreadPoolExecutorPlus import ThreadPoolExecutor
from types import CoroutineType
from sqlalchemy.exc import TimeoutError
import asyncio

class AsyncConnectionContextManager:

    def __init__(self , 
        coro: CoroutineType, 
        loop: Optional[asyncio.BaseEventLoop] = None, 
        executor: Optional[ThreadPoolExecutor] = None,
        engine: Optional[Engine] = None,
    ):
        self._coro = coro
        self._loop = loop
        self._executor = executor
        self._engine = engine
        self._obj = None

    def __iter__(self):
        return self._coro.__await__()

    def __await__(self):
        return self._coro.__await__()

    async def __aenter__(self):
        try:
            self._obj = AsyncConnectionWrapper(await self._coro, self._loop, self._executor)
        except TimeoutError as e:
            self._obj = AsyncConnectionWrapper(None)
        return self._obj

    async def __aexit__(self, *args):
        await self._obj.close()
        if self._executor is not None:
            self._engine.pending -= 1
        self._obj = None


class AsyncConnectionWrapper:
    
    def __init__(self, 
        connection: Optional[Connection] = None, 
        loop: Optional[asyncio.BaseEventLoop] = None, 
        executor: Optional[ThreadPoolExecutor] = None
    ):
        self.connection = connection
        self._loop = loop
        self._executor = executor
        self._cross_thread_protect_thread: bool = False
        if self.connection:
            self._unavailable = False
        else:
            self._unavailable = True

    def unavailable(self):
        return self._unavailable

    async def exclusionary_connection(self, coro: CoroutineType):

        if self._cross_thread_protect_thread:
            raise RuntimeError('Since sqlalchemy.engine.Connection is not thread-safe, you cannot share connections between coroutine threads in this particular scenario. If concurrency is required, please open plural connections.')
        self._cross_thread_protect_thread = True
        try:
            return await coro
        finally:
            self._cross_thread_protect_thread = False
    
    async def _select_one_impl(self, sql: str, args: Iterable[Any] = (), executemany: bool = False):

        def execute_and_fetch(conn, sql, args, executemany):
            sender = conn.execute if not executemany else conn.executemany
            cur = sender(text(sql), args)
            return cur.fetchone()
        return await self._loop.run_in_executor(self._executor, execute_and_fetch, self.connection, sql, args, executemany)

    async def select_one(self, *args, **kwargs):
        return await self.exclusionary_connection(self._select_one_impl(*args, **kwargs))

    async def _select_all_impl(self, sql: str, args: Iterable[Any] = (), executemany: bool = False):

        def execute_and_fetch(conn, sql, args, executemany):
            sender = conn.execute if not executemany else conn.executemany
            cur = sender(text(sql), args)
            return cur.fetchall()
        return await self._loop.run_in_executor(self._executor, execute_and_fetch, self.connection, sql, args, executemany)

    async def select_all(self, *args, **kwargs):
        return await self.exclusionary_connection(self._select_all_impl(*args, **kwargs))

    async def _execute_and_commit_impl(self, sql: str, args: Iterable[Any] = (), executemany: bool = False):

        def eac(conn, sql, args, executemany):
            sender = conn.execute if not executemany else conn.executemany
            sender(text(sql), args)
            return conn.commit()
        return await self._loop.run_in_executor(self._executor, eac, self.connection, sql, args, executemany)

    async def execute_and_commit(self, *args, **kwargs):
        return await self.exclusionary_connection(self._execute_and_commit_impl(*args, **kwargs))

    async def execute(self, sql: str, args: Iterable[Any] = (), executemany: bool = False):
        return await self.exclusionary_connection(self._loop.run_in_executor(self._executor, self.connection.execute if not executemany else self.connection.executemany, text(sql), args))

    async def commit(self):
        return await self.exclusionary_connection(self._loop.run_in_executor(self._executor, self.connection.commit))

    async def fetchone(self):
        return await self.exclusionary_connection(self._loop.run_in_executor(self._executor, self.connection.fetchone))

    async def fetchall(self):
        return await self.exclusionary_connection(self._loop.run_in_executor(self._executor, self.connection.fetchall))

    async def close(self):
        if self._unavailable:
            return 
        return await self._loop.run_in_executor(self._executor, self.connection.close)