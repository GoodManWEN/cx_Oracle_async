import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
from cx_Oracle_async import *

@pytest.mark.asyncio
async def test_different_connect_ways():
    dsn = makedsn(
        host = 'localhost', 
        port = '1521', 
        sid = 'xe'
    )
    oracle_pool = await create_pool(
        user = 'system',
        password = 'oracle',
        dsn = dsn
    )
    ret = await oracle_pool.close()
    assert ret == None

    oracle_pool = await create_pool(
        host = 'localhost',
        port = '1521',
        user = 'system',
        password = 'oracle',
        sid = 'xe',
        min = 2 ,
        max = 4
    )

    async with oracle_pool.acquire() as connection:
        async with connection.cursor() as cursor:
            pass

    ret = await oracle_pool.close()
    assert ret == None
    