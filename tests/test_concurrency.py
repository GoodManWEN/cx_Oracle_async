import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
import time
from cx_Oracle_async import *

@pytest.mark.asyncio
async def test_multiquery():

    CQUANT = 16
    INAC = 0.5
    SLEEP_TIME = 5

    async def single_thread(oracle_pool , counter):
        async with oracle_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute('BEGIN  DBMS_LOCK.SLEEP(:a); END;' , (SLEEP_TIME, ))
                counter[0] += 1

    
    dsn  = makedsn('localhost','1521',sid='xe')
    async with create_pool(user='system',password='oracle',dsn=dsn,max=CQUANT) as oracle_pool:

        # under limit test
        counter = [0 , ]
        st_time = time.time()
        await asyncio.gather(*(single_thread(oracle_pool , counter) for _ in range(CQUANT)))
        ed_time = time.time()
        assert counter[0] == CQUANT
        assert (SLEEP_TIME - INAC) <= (ed_time - st_time) <= (CQUANT * SLEEP_TIME // 2 + INAC)

        # overflow test
        counter = [0 , ]
        st_time = time.time()
        await asyncio.gather(*(single_thread(oracle_pool , counter) for _ in range(CQUANT + 1)))
        ed_time = time.time()
        assert counter[0] == CQUANT + 1
        assert (SLEEP_TIME * 2 - INAC) <= (ed_time - st_time) <= (SLEEP_TIME * 3 + INAC)