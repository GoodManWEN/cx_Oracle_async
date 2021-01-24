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
        async with oracle_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                # check if dept exesits
                await cursor.execute("SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = UPPER(:a)" , ('DEPT' , ))
                ret = await cursor.fetchone()
                assert ret 
                if ret[0] > 0:
                    await cursor.execute("DROP TABLE DEPT")

                sql = f"""
                    CREATE TABLE DEPT
                       (DEPTNO NUMBER(2) CONSTRAINT PK_DEPT PRIMARY KEY,
                        DNAME VARCHAR2(14),
                        LOC VARCHAR2(13) 
                    )
                """
                await cursor.execute(sql)

                await cursor.execute(f"INSERT INTO DEPT(DEPTNO) VALUES (:a)" , (10 , ))
                await conn.rollback()
                await cursor.execute(f"INSERT INTO DEPT(DEPTNO) VALUES (:a)" , (12 , ))
                await conn.commit()

        async with oracle_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(f"SELECT * FROM DEPT")
                r = await cursor.fetchall()
                assert len(r) == 1
                assert r[0][0] == 12