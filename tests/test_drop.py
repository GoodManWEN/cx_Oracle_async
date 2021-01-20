import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
import time
from cx_Oracle_async import *
import cx_Oracle

async def create_long_query(oracle_pool):
    async with oracle_pool.acquire() as conn:
        cursor = await conn.cursor()
        try:
            await cursor.execute("BEGIN  DBMS_LOCK.SLEEP(:a); END;",(20,))
        except Exception as e:
            assert isinstance(e , cx_Oracle.OperationalError)

@pytest.mark.asyncio
async def test_force_close():
    loop = asyncio.get_running_loop()
    dsn  = makedsn('localhost','1521',sid='xe')
    INAQ = 0.5
    oracle_pool = await create_pool(user='system',password='oracle',dsn=dsn,max=4)
    loop = asyncio.get_running_loop()
    loop.create_task(create_long_query(oracle_pool))
    st_time = time.time()
    await asyncio.sleep(2)
    await oracle_pool.close(force = True)
    ed_time = time.time()
    assert (ed_time - st_time) <= (20 - INAQ)