from cx_Oracle import MessageProperties , DEQ_NO_WAIT 
from ThreadPoolExecutorPlus import ThreadPoolExecutor
from asyncio import Lock as aioLock
from collections.abc import Iterable
from typing import Union , TYPE_CHECKING
if TYPE_CHECKING:
    from .connections import AsyncConnectionWrapper
    from cx_Oracle import Queue
    from asyncio.windows_events import ProactorEventLoop


class AsyncQueueWrapper:
    
    def __init__(self , queue: 'Queue', loop: 'ProactorEventLoop' , thread_pool: ThreadPoolExecutor , conn : 'AsyncConnectionWrapper'):
        self._queue = queue
        self._loop = loop
        self._thread_pool = thread_pool 
        self._conn = conn
        self._deqlock = aioLock()

    async def enqOne(self , *args , **kwargs):
        return await self._loop.run_in_executor(self._thread_pool , self._queue.enqOne , *args , **kwargs)

    async def enqMany(self , *args , **kwargs):
        return await self._loop.run_in_executor(self._thread_pool , self._queue.enqMany , *args , **kwargs)

    async def deqOne(self , *args , **kwargs):
        async with self._deqlock:
            return await self._loop.run_in_executor(self._thread_pool , self._queue.deqOne , *args , **kwargs)

    def deqMany(self , maxMessages: int = -1):
        return DeqManyWrapper(self._loop , self._thread_pool , self._queue , self._deqlock , maxMessages)

    def _decode(self , _object: MessageProperties):
        return _object.payload.decode(self._conn.encoding)

    def unpack(self , _object: Union[MessageProperties , list]):
        if isinstance(_object , Iterable):
            return list(map(self._decode , _object))
        else:
            return self._decode(_object)

    @property
    def pack(self):
        return self._conn.msgproperties

    @property
    def enqOptions(self):
        return self._queue.enqOptions
    
    @property
    def deqOptions(self):
        return self._queue.deqOptions


class DeqManyWrapper:

    def __init__(self , loop : 'ProactorEventLoop' , thread_pool : ThreadPoolExecutor, queue : 'Queue' , deqlock: aioLock , maxMessages : int):
        self._loop = loop
        self._thread_pool = thread_pool
        self._queue = queue
        self._count = 0
        self._max = maxMessages if maxMessages > -1 else (1 << 16 - 1) 
        self._max = self._max if self._max <= (1 << 16 - 1) else (1 << 16 - 1) 
        self._deqlock = deqlock

    def __await__(self):
        yield from self._deqlock.acquire().__await__()
        try:
            ret = yield from self._loop.run_in_executor(self._thread_pool , self._queue.deqMany , self._max).__await__()
        except Exception as exc:
            raise exc
        finally:
            self._deqlock.release()
        return ret

    def __aiter__(self):
        return self

    async def __anext__(self):
        self._count += 1
        if self._count <= self._max:
            _tmp = self._queue.deqOptions.wait
            async with self._deqlock:
                self._queue.deqOptions.wait = DEQ_NO_WAIT
                data = await self._loop.run_in_executor(self._thread_pool , self._queue.deqOne)
                self._queue.deqOptions.wait = _tmp
            if data:
                return data
            else:
                raise StopAsyncIteration
        else:
            raise StopAsyncIteration