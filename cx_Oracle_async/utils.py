from ThreadPoolExecutorPlus import ThreadPoolExecutor
import cx_Oracle as cxor
import platform
import asyncio
import os

pltfm = platform.system()
if pltfm == 'Windows':
    DEFAULT_MAXIMUM_WORKER_NUM = (os.cpu_count() or 1) * 16
    DEFAULT_MAXIMUM_WORKER_TIMES = 2
elif pltfm == 'Linux' or pltfm == 'Darwin':
    DEFAULT_MAXIMUM_WORKER_NUM = (os.cpu_count() or 1) * 32
    DEFAULT_MAXIMUM_WORKER_TIMES = 3

makedsn = cxor.makedsn

class AsyncCursorWrapper:

    def __init__(self , loop , thread_pool , cursor):
        self._loop = loop
        self._thread_pool = thread_pool
        self._cursor = cursor

    async def execute(self , sql , args = None):
        if args == None:
            await self._loop.run_in_executor(self._thread_pool , self._cursor.execute , sql)
        else:
            await self._loop.run_in_executor(self._thread_pool , self._cursor.execute , sql , args)

    async def executemany(self , sql , args = None):
        if args == None:
            await self._loop.run_in_executor(self._thread_pool , self._cursor.executemany , sql)
        else:
            await self._loop.run_in_executor(self._thread_pool , self._cursor.executemany , sql , args)

    async def fetchall(self):
        # block mainly happens when fetch triggered.
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.fetchall)

    async def fetchone(self):
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.fetchone)

    async def var(self, args):
        return await self._loop.run_in_executor(self._thread_pool , self._cursor.var, args)


class AsyncCursorWrapper_context:

    def __init__(self , loop , thread_pool , conn):
        self._loop = loop
        self._thread_pool = thread_pool
        self._conn = conn

    async def __aenter__(self):
        cursor = await self._loop.run_in_executor(self._thread_pool , self._conn.cursor)
        return AsyncCursorWrapper(self._loop , self._thread_pool , cursor)

    async def __aexit__(self, exc_type, exc, tb):
        return

class AsyncConnectionWrapper:

    def __init__(self , loop , thread_pool , conn):
        self._loop = loop
        self._thread_pool = thread_pool
        self._conn = conn 

    def cursor(self):
        return AsyncCursorWrapper_context(self._loop , self._thread_pool , self._conn)

    async def commit(self):
        await self._loop.run_in_executor(self._thread_pool , self._conn.commit)

class AsyncConnectionWrapper_context:

    def __init__(self , loop , thread_pool , pool ):
        self._loop = loop
        self._thread_pool = thread_pool
        self._pool = pool 

    async def __aenter__(self):
        self._conn = await self._loop.run_in_executor(self._thread_pool , self._pool.acquire) 
        return AsyncConnectionWrapper(self._loop , self._thread_pool , self._conn)

    async def __aexit__(self, exc_type, exc, tb):
        await self._loop.run_in_executor(self._thread_pool , self._pool.release , self._conn)

class AsyncPoolWrapper:
    
    def __init__(self , pool , loop = None):
        
        if loop == None:
            loop = asyncio.get_running_loop()
        '''
        Generally speaking , usually we need a context manager to make thread pool and 
        oracle connection pool greacefully shutdown , however I find no means to 
        implementation it implicitly (Which means user have to start a 'with' statement 
        everytime they call create_pool , I don't take it as a good idea.)

        Issue if you have better implementation.
        '''
        self._thread_pool = ThreadPoolExecutor(max_workers = max(DEFAULT_MAXIMUM_WORKER_NUM , pool.max << DEFAULT_MAXIMUM_WORKER_TIMES)) 
        self._thread_pool.set_daemon_opts(min_workers = max(4 , pool.min << 1))
        self._loop = loop 
        self._pool = pool 

    def acquire(self):
        return AsyncConnectionWrapper_context(self._loop , self._thread_pool , self._pool)

    async def close(self):
        return await self._loop.run_in_executor(self._thread_pool , self._pool.close)

    async def preexciting(self):

        def _test():
            ...

        await self._loop.run_in_executor(self._thread_pool , _test)

async def create_pool(
        user=None, 
        password=None, 
        dsn=None, 
        min=2, 
        max=4, 
        increment=1, 
        connectiontype=cxor.Connection, 
        threaded=True, 
        getmode=cxor.SPOOL_ATTRVAL_NOWAIT, 
        events=False, 
        homogeneous=True, 
        externalauth=False, 
        encoding='UTF-8', 
        edition=None, 
        timeout=0, 
        waitTimeout=0, 
        maxLifetimeSession=0, 
        sessionCallback=None, 
        maxSessionsPerShard=0,
        host=None,
        port=None,
        service_name=None,
        sid=None,
        loop=None
    ):
    if loop == None:
        loop = asyncio.get_running_loop()
    if dsn == None:
        if service_name != None:
            dsn = makedsn(host = host, port = port, sid = sid , service_name = service_name)
        else:
            dsn = makedsn(host = host, port = port, sid = sid)
    pool = cxor.SessionPool(
        user=user, 
        password=password, 
        dsn=dsn, 
        min=min, 
        max=max, 
        increment=increment, 
        connectiontype=connectiontype, 
        threaded=threaded, 
        getmode=getmode, 
        events=events, 
        homogeneous=homogeneous, 
        externalauth=externalauth, 
        encoding=encoding, 
        edition=edition, 
        timeout=timeout, 
        waitTimeout=waitTimeout, 
        maxLifetimeSession=maxLifetimeSession, 
        sessionCallback=sessionCallback, 
        maxSessionsPerShard=maxSessionsPerShard)
    pool = AsyncPoolWrapper(pool)
    await pool.preexciting()
    return pool

async def __test():
    ...

if __name__ == '__main__':
    asyncio.run(__test())
