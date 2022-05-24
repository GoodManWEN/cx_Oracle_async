from sqlalchemy.engine import Engine
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from functools import partial, wraps
from typing import Optional, Type, Any
from numbers import Number
from os import cpu_count
from ThreadPoolExecutorPlus import ThreadPoolExecutor
from types import CoroutineType
import asyncio
import platform

from .connections import AsyncConnectionContextManager

pltfm = platform.system()
if pltfm == 'Windows':
    DEFAULT_MAXIMUM_WORKER_NUM = (cpu_count() or 1) * 16
    DEFAULT_MAXIMUM_WORKER_TIMES = 4
elif pltfm == 'Linux' or pltfm == 'Darwin':
    DEFAULT_MAXIMUM_WORKER_NUM = (cpu_count() or 1) * 32
    DEFAULT_MAXIMUM_WORKER_TIMES = 6

class Pathcer:

    def __init__(self):
        super(Pathcer, self).__init__()
        
    def patch(self, engine: Engine):

        def _close(self: Engine):
            self._closing = True
            self._conn_to_close = self.pool.checkedin() + self.pool.checkedout()

        async def _wait_closed(self: Engine):
            def tmp(engine):
                for _ in range(engine._conn_to_close):
                    engine.pool._pool.get().close()
            coro = self._loop.run_in_executor(self._thread_pool_executor, tmp, engine)
            return await coro

        engine._loop = None
        engine._closing = False
        engine._conn_to_close = 0
        max_workers = max(DEFAULT_MAXIMUM_WORKER_NUM , engine.pool.size() << DEFAULT_MAXIMUM_WORKER_TIMES)
        engine._thread_pool_executor = ThreadPoolExecutor(max_workers = max_workers)
        engine._thread_pool_executor.set_daemon_opts(min_workers = 2)
        engine.close = partial(_close, self=engine)
        engine.wait_closed = partial(_wait_closed, self=engine)
        engine.acquire = partial(self.__class__.acquire, engine=engine)
        engine.pending: int = 0
        engine.max_pending_allowed: int = max(max_workers - engine.pool.size(), 1)

    def acquire(engine):
        loop = engine._loop
        if loop is None:
            engine._loop = loop = asyncio.get_running_loop()
        
        if engine._closing or engine.pending >= engine.max_pending_allowed:
            async def tmp():
                return None 
            return AsyncConnectionContextManager(tmp())
        # else 
        engine.pending += 1 
        coro = loop.run_in_executor(engine._thread_pool_executor, engine.connect)
        return AsyncConnectionContextManager(coro, loop, engine._thread_pool_executor, engine)


def _create_connect_string(host, port, sid, service_name, user, password, encoding, nencoding):
    user_pass = f"{user}{':' if password else ''}{password}"
    host_port = f"{host}{':' if port else ''}{port}"
    additional = f"{sid}{'?' if service_name or encoding or nencoding else ''}"
    has_params = False 
    for name, name_str in [[service_name, 'service_name'], [encoding, 'encoding'], [nencoding, 'nencoding']]:
        if name:
            if has_params:
                additional += '&'
            additional += f"{name_str}={name}"
            has_params = True
    return f"oracle+cx_oracle://{user_pass}{'@' if user_pass else ''}{host_port}{'/' if additional else ''}{additional}"

def create_pool(
    host: str = 'localhost',
    port: str | int = 1521,
    sid: Optional[str] = None,
    service_name: Optional[str] = None,
    user: Optional[str] = None,
    password: Optional[str] = None,
    encoding: Optional[str] = None,
    nencoding: Optional[str] = None,
    pool_size: Optional[int] = None,
    max_overflow: Optional[int] = None,
    pool_timeout: Type[Number] = 30.0,
    pool_recycle: Type[Number] = 3600,
    pool_use_lifo: bool = True,
    pool_pre_ping: bool = True,
    echo: bool = False, 
    echo_pool: bool = False,
):
    if isinstance(port, str):
        port = int(port) 
    if sid is None:
        sid = ''
    if service_name is None:
        service_name = ''  
    if user is None:
        user = ''
    if password is None:
        password = ''
    if encoding is None:
        encoding = 'UTF-8'
    encoding = encoding.upper()
    if nencoding is None:
        nencoding = encoding
    nencoding = nencoding.upper()
    if pool_size is None:
        pool_size = cpu_count() or 1
    if max_overflow is None:
        max_overflow = pool_size

    connect_string: str = _create_connect_string(host, port, sid, service_name, user, password, encoding, nencoding)
    engine = create_engine(
        connect_string,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        echo=echo, 
        echo_pool=echo_pool, 
        future=True,                     
        poolclass=QueuePool,
        pool_use_lifo=True,              
        pool_pre_ping=True,              
    )
    Pathcer().patch(engine)
    return engine




