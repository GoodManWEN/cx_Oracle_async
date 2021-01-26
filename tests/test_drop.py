import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
import time
from async_timeout import timeout
from cx_Oracle_async import *
import cx_Oracle
import threading

async def create_long_query(oracle_pool):
    async with oracle_pool.acquire() as conn:
        cursor = await conn.cursor()
        try:
            await cursor.execute("BEGIN  DBMS_LOCK.SLEEP(:a); END;",(10,))
        except Exception as e:
            assert isinstance(e , cx_Oracle.OperationalError)

def create_long_query_sync(oracle_pool):
    '''
    use sync function in order to avoid pytest loop never stop bug.
    '''
    try:
        conn = oracle_pool._pool.acquire()
        cursor = conn.cursor()
        cursor.execute("BEGIN  DBMS_LOCK.SLEEP(:a); END;",(10,))
    except:
        ...

@pytest.mark.asyncio
async def test_force_close():
    loop = asyncio.get_running_loop()
    dsn  = makedsn('localhost','1521',sid='xe')
    INAQ = 0.5
    oracle_pool = await create_pool(user='system',password='oracle',dsn=dsn)
    loop.create_task(create_long_query(oracle_pool))
    st_time = time.time()
    await asyncio.sleep(2)
    await oracle_pool.close(force = True , interrupt = False)
    ed_time = time.time()
    assert (10 - INAQ) <= (ed_time - st_time) <= (10 + INAQ)

    # test occupy
    oracle_pool = await create_pool(user='system',password='oracle',dsn=dsn,max=4)
    conn1 = await oracle_pool.acquire()
    conn2 = await oracle_pool.acquire()
    assert len(oracle_pool._occupied) == 2
    conn3 = await oracle_pool.acquire()
    assert len(oracle_pool._occupied) == 3
    st_time = time.time()
    await asyncio.sleep(2)
    async with timeout(2):
        # no running task , return immediately
        await oracle_pool.close(force = True , interrupt = False)
    ed_time = time.time()
    assert (2 - INAQ) <= (ed_time - st_time) <= (2 + INAQ)

    # test interrupt
    oracle_pool = await create_pool(user='system',password='oracle',dsn=dsn,max=4)
    st_time = time.time()
    t = threading.Thread(target = create_long_query_sync , args = (oracle_pool,))
    t.setDaemon(True)
    t.start()
    await asyncio.sleep(2)
    exception_flag = False
    try:
        async with timeout(2):
            # no response forever
            await oracle_pool.close(force = True , interrupt = True)
    except Exception as e:
        exception_flag = True
        assert isinstance(e , asyncio.TimeoutError)
    ed_time = time.time()
    assert exception_flag
    assert (4 - INAQ) <= (ed_time - st_time) <= (10 - INAQ)