import cx_Oracle
from asyncio import Lock as aioLock


class AsyncQueueWrapper:
    
    def __init__(self , queue , loop , thread_pool , ):
        self._queue = queue
        self._loop = loop
        self._thread_pool = thread_pool 
        self._deqlock = aioLock()

    async def enqOne(self , *args , **kwargs):
        return await self._loop.run_in_executor(self._thread_pool , self._queue.enqOne , *args , **kwargs)

    async def enqMany(self , *args , **kwargs):
        return await self._loop.run_in_executor(self._thread_pool , self._queue.enqMany , *args , **kwargs)

    async def deqOne(self , *args , **kwargs):
        async with self._deqlock:
            return await self._loop.run_in_executor(self._thread_pool , self._queue.deqOne , *args , **kwargs)

    def deqMany(self , maxMessages = -1):
        return DeqManyWrapper(self._loop , self._thread_pool , self._queue , self._deqlock , maxMessages)

    @property
    def enqOptions(self):
        return self._queue.enqOptions
    
    @property
    def deqOptions(self):
        return self._queue.deqOptions


class DeqManyWrapper:

    def __init__(self , loop , thread_pool , queue , deqlock ,maxMessages):
        self._loop = loop
        self._thread_pool = thread_pool
        self._queue = queue
        self._count = 0
        self._max = maxMessages if maxMessages != -1 else (1 << 16 - 1) 
        self._deqlock = deqlock

    def __await__(self):
        return self._loop.run_in_executor(self._thread_pool , self._queue.deqMany , self._max).__await__()

    def __aiter__(self):
        return self

    async def __anext__(self):
        self._count += 1
        if self._count <= self._max:
            _tmp = self._queue.deqOptions.wait
            async with self._deqlock:
                self._queue.deqOptions.wait = cx_Oracle.DEQ_NO_WAIT
                data = await self._loop.run_in_executor(self._thread_pool , self._queue.deqOne)
                self._queue.deqOptions.wait = _tmp
            if data:
                return data
            else:
                raise StopAsyncIteration
        else:
            raise StopAsyncIteration