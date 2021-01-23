import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
from cx_Oracle_async import *
import cx_Oracle

@pytest.mark.asyncio
async def test_ping():
    dsn = makedsn(
        host = 'localhost', 
        port = '1521', 
        sid = 'xe'
    )
    async with create_pool(user = 'system',password = 'oracle',dsn = dsn) as oracle_pool:
        conn = await oracle_pool.acquire()
        r = await conn.ping()
        assert r == None

        await conn.release()
        exception_flag = False
        try:
            await conn.ping()
        except Exception as e:
            exception_flag = True
            assert isinstance(e , cx_Oracle.InterfaceError)
        assert exception_flag
