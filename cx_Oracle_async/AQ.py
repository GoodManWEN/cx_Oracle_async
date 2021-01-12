from cx_Oracle import MessageProperties , DEQ_NO_WAIT 
from ThreadPoolExecutorPlus import ThreadPoolExecutor
from asyncio import Lock as aioLock
from collections.abc import Iterable
from typing import Union , TYPE_CHECKING
from collections import deque
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
        self._max_messages = maxMessages
        self._deqlock = deqlock
        self._buffer = deque()
        self._soft_max = ((1 << 16) - 1)
        self._max_limit = maxMessages if maxMessages > -1 else self._soft_max
        self._max_limit = self._max_limit if self._max_limit <= self._soft_max else self._soft_max 
        self._deqcount = 0
        self._closed = False

    @property 
    def _fetch_num(self):
        return self._soft_max if self._max_messages < 0 else min(self._max_limit , self._max_messages - self._deqcount)

    def __await__(self):
        if self._closed:
            raise RuntimeError('Current query has closed , you cannot activate it twice.')
        yield from self._deqlock.acquire().__await__()
        try:
            ret = yield from self._loop.run_in_executor(self._thread_pool , self._queue.deqMany , self._fetch_num).__await__()
        except Exception as exc:
            raise exc
        finally:
            self._deqlock.release()
        self._closed = True
        return ret

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._closed:
            raise RuntimeError('Current query has closed , you cannot activate it twice.')

        if self._max_messages == 0:
            self._closed = True
            raise StopAsyncIteration

        # Fetch off
        if self._max_messages > 0 and self._deqcount >= self._max_messages:
            if self._buffer:
                return self._buffer.popleft()
            self._closed = True
            raise StopAsyncIteration

        # Fetch on
        if self._buffer:
            return self._buffer.popleft()
        _tmp = self._queue.deqOptions.wait
        async with self._deqlock:
            try:
                self._queue.deqOptions.wait = DEQ_NO_WAIT
                data = await self._loop.run_in_executor(self._thread_pool , self._queue.deqMany , self._fetch_num)
            except Exception as exc:
                raise exc
            finally:
                self._queue.deqOptions.wait = _tmp

            if data:
                self._buffer.extend(data)
                self._deqcount += len(data)
                return self._buffer.popleft()

            # No data return , close iteration.
            self._closed = True
            raise StopAsyncIteration