import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
from cx_Oracle_async import *

@pytest.mark.asyncio
async def test_new_table():
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
    
    async with oracle_pool.acquire() as connection:
        async with connection.cursor() as cursor:
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

            # Single Insertion 
            sql = "INSERT INTO DEPT(DEPTNO , DNAME , LOC) VALUES (:a , :b , :c)"
            await cursor.execute(sql , (10 ,'ACCOUNTING','NEW YORK'))
            await connection.commit()

            # bind vars
            sql = "SELECT DNAME FROM DEPT WHERE DEPTNO = :dno"
            await cursor.execute(sql , dno = 10)
            ret = await cursor.fetchone()
            assert ret
            assert ret[0] == 'ACCOUNTING'

            # Multiple Insertion
            sql = "INSERT INTO DEPT(DEPTNO , DNAME , LOC) VALUES (:a , :b , :c)"
            data = [
                (30,'SALES','CHICAGO'),
                (40,'OPERATIONS','BOSTON'),
            ]
            await cursor.executemany(sql , data)
            await connection.commit()

            # Check
            await cursor.execute("SELECT DNAME , LOC FROM DEPT WHERE DEPTNO BETWEEN :a AND :b" , (10 , 30))
            ret = await cursor.fetchall()
            assert len(ret) == 2
            assert ret[0][0] == 'ACCOUNTING'
            assert ret[1][1] == 'CHICAGO'

    await oracle_pool.close()

@pytest.mark.asyncio
async def test_usage():
    dsn = makedsn(
        host = 'localhost', 
        port = '1521', 
        sid = 'xe'
    )
    oracle_pool1 = await create_pool(
        user = 'system',
        password = 'oracle',
        dsn = dsn
    )
    async with create_pool(user = 'system',password = 'oracle',dsn = dsn) as oracle_pool2:
        assert type(oracle_pool1) is type(oracle_pool2)

    conn1 = await oracle_pool1.acquire()
    async with oracle_pool1.acquire() as conn2:
        assert type(conn1) is type(conn2)

    cursor1 = await conn1.cursor()
    async with conn1.cursor() as cursor2:
        assert type(cursor1) is type(cursor2)

    conn = await oracle_pool1.acquire()
    await conn.release()
    conn = await oracle_pool1.acquire()
    await oracle_pool1.release(conn)
    
    # test weakref
    conn = await oracle_pool1.acquire()
    conn = await oracle_pool1.acquire()
    conn = await oracle_pool1.acquire()
    assert len(oracle_pool1._occupied) == 2
