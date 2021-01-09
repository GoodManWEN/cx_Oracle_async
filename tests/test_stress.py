import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
import time
from cx_Oracle_async import *

class Status:

    def __init__(self):
        self.status = True

async def single_fetch(oracle_pool , n_data = 70):
    async with oracle_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"INSERT INTO DEPT(DEPTNO) VALUES (:a)" , (n_data , ))
            await conn.commit()

    async with oracle_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"SELECT DEPTNO FROM DEPT WHERE DEPTNO = :a" , (n_data , ))
            ret = await cursor.fetchone()
            assert ret 
            assert ret[0] == n_data
            await conn.commit()

    async with oracle_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"DELETE FROM DEPT WHERE DEPTNO = :a" , (n_data , ))
            await conn.commit()
            
    async with oracle_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute(f"SELECT DEPTNO FROM DEPT WHERE DEPTNO = :a" , (n_data , ))
            ret = await cursor.fetchone()
            assert ret == None
            await conn.commit()

async def single_thread(oracle_pool , n_data , status):
    while status.status:
        await single_fetch(oracle_pool , n_data)

async def daemon_thread(status):
    await asyncio.sleep(60)
    status.status = False

@pytest.mark.asyncio
async def test_multiquery():
    dsn  = makedsn('localhost','1521',sid='xe')
    max_thread = min(max(int((os.cpu_count() or 1) // 2) , 2) , 8)
    start_number = 77
    oracle_pool = await create_pool(user='system',password='oracle',dsn=dsn,max=max_thread)
    async with oracle_pool.acquire() as conn:
        async with conn.cursor() as cursor:
            await cursor.execute("SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = UPPER(:a)" , ('DEPT' , ))
            ret = await cursor.fetchone()
            assert ret 
            if ret[0] <= 0:
                sql = f"""
                        CREATE TABLE DEPT
                           (DEPTNO NUMBER(2) CONSTRAINT PK_DEPT PRIMARY KEY,
                            DNAME VARCHAR2(14),
                            LOC VARCHAR2(13) 
                        )
                    """
                try:
                    await cursor.execute(sql)
                    await cursor.execute(f"DELETE FROM DEPT WHERE DEPTNO >= :a" , (start_number , ))
                    await conn.commit()
                except:
                    pass
            else:
                await cursor.execute(f"DELETE FROM DEPT WHERE DEPTNO >= :a" , (start_number , ))
                await conn.commit()
    status = Status()
    loop = asyncio.get_running_loop()
    loop.create_task(daemon_thread(status))
    await asyncio.gather(*(single_thread(oracle_pool , start_number + _ , status) for _ in range(max_thread * 2)))
    await oracle_pool.close()