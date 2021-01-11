from .pools import AsyncPoolWrapper , AsyncPoolWrapper_context
from ThreadPoolExecutorPlus import ThreadPoolExecutor
import cx_Oracle as cxor
import asyncio
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from asyncio.windows_events import ProactorEventLoop


makedsn = cxor.makedsn
DEQ_NO_WAIT = cxor.DEQ_NO_WAIT
DEQ_WAIT_FOREVER = cxor.DEQ_WAIT_FOREVER

async def _create_pool(
        host: str =None,
        port: str =None,
        service_name: str =None,
        sid: str =None,
        loop: 'ProactorEventLoop' =None,
        dsn: str =None,
        **kwargs
    ):
    if loop == None:
        loop = asyncio.get_running_loop()

    if dsn == None:
        if service_name != None:
            dsn = makedsn(host = host, port = port, sid = sid , service_name = service_name)
        else:
            dsn = makedsn(host = host, port = port, sid = sid)
    pool = cxor.SessionPool(dsn=dsn, **kwargs)
    pool = AsyncPoolWrapper(pool)
    return pool

def create_pool(
        user: str =None, 
        password: str =None, 
        dsn: str =None, 
        min: int =2, 
        max: int =4, 
        increment=1, 
        connectiontype=cxor.Connection, 
        threaded=True, 
        getmode=cxor.SPOOL_ATTRVAL_WAIT, 
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
        host: str =None,
        port: str =None,
        service_name: str =None,
        sid: str =None,
        loop: 'ProactorEventLoop' =None,
    ):
    coro = _create_pool(
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
        maxSessionsPerShard=maxSessionsPerShard,
        host=host,
        port=port,
        service_name=service_name,
        sid=sid,
        loop=loop,
    )
    return AsyncPoolWrapper_context(coro)