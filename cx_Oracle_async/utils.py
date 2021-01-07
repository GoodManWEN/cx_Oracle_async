from ThreadPoolExecutorPlus import ThreadPoolExecutor
import cx_Oracle as csor
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

class AsyncCursorWarpper:

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


class AsyncCursorWarpper_context:

    def __init__(self , loop , thread_pool , conn):
        self._loop = loop
        self._thread_pool = thread_pool
        self._conn = conn

    async def __aenter__(self):
        cursor = await self._loop.run_in_executor(self._thread_pool , self._conn.cursor)
        return AsyncCursorWarpper(self._loop , self._thread_pool , cursor)

    async def __aexit__(self, exc_type, exc, tb):
        return

class AsyncConnectionWarpper:

    def __init__(self , loop , thread_pool , conn):
        self._loop = loop
        self._thread_pool = thread_pool
        self._conn = conn 

    def cursor(self):
        return AsyncCursorWarpper_context(self._loop , self._thread_pool , self._conn)

    async def commit(self):
        await self._loop.run_in_executor(self._thread_pool , self._conn.commit)

class AsyncConnectionWarpper_context:

    def __init__(self , loop , thread_pool , pool ):
        self._loop = loop
        self._thread_pool = thread_pool
        self._pool = pool 

    async def __aenter__(self):
        self._conn = await self._loop.run_in_executor(self._thread_pool , self._pool.acquire) 
        return AsyncConnectionWarpper(self._loop , self._thread_pool , self._conn)

    async def __aexit__(self, exc_type, exc, tb):
        await self._loop.run_in_executor(self._thread_pool , self._pool.release , self._conn)

class AsyncPoolWarpper:
    
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
        return AsyncConnectionWarpper_context(self._loop , self._thread_pool , self._pool)

    async def close(self):
        return await self._loop.run_in_executor(self._thread_pool , self._pool.close)

    async def preexciting(self):

        def _test():
            ...

        await self._loop.run_in_executor(self._thread_pool , _test)

async def create_pool(host = 'localhost', port = '1521' , user = 'sys', password = '', db = 'orcl', loop = None, minsize = 2 , maxsize = 4 , encoding = 'UTF-8' , autocommit=False):
    if loop == None:
        loop = asyncio.get_running_loop()
    pool = csor.SessionPool(user , password , f"{host}:{port}/{db}", min = minsize , max = maxsize , increment = 1 , threaded = True , encoding = encoding)
    pool = AsyncPoolWarpper(pool)
    await pool.preexciting()
    return pool

async def __test():
    ...

if __name__ == '__main__':
    asyncio.run(__test())
