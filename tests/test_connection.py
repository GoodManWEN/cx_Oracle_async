import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
from cx_Oracle_async import *
import time

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
    
@pytest.mark.asyncio
async def test_properties():
    INAQ = 0.5
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

    async with oracle_pool.acquire() as conn:
        st_time = time.time()
        conn.module = 'hello world'
        conn.action = 'test_action'
        conn.client_identifier = 'test_identifier'
        conn.clientinfo = 'test_info'
        ed_time = time.time()
        assert (ed_time - st_time) <= INAQ

        async with conn.cursor() as cursor:
            await cursor.execute("SELECT SID, MODULE ,ACTION ,CLIENT_IDENTIFIER , CLIENT_INFO FROM V$SESSION WHERE MODULE='hello world'")
            r = await cursor.fetchall()
            assert len(r) == 1
            _ , _module , _action , _ciden , _cinfo = r[0]
            assert _module == 'hello world'
            assert _action == 'test_action'
            assert _ciden == 'test_identifier'
            assert _cinfo == 'test_info'

        # test no update 
        st_time = time.time()
        conn.module = 'hello world2'
        conn.action = 'test_action2'
        conn.client_identifier = 'test_identifier2'
        conn.clientinfo = 'test_info2'
        ed_time = time.time()
        assert (ed_time - st_time) <= INAQ

        conn2 = await oracle_pool.acquire()
        async with conn2.cursor() as cursor:
            await cursor.execute("SELECT SID, MODULE ,ACTION ,CLIENT_IDENTIFIER , CLIENT_INFO FROM V$SESSION WHERE MODULE='hello world2'")
            r = await cursor.fetchall()
            assert len(r) == 0