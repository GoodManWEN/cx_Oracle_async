.. _sqlexecution:

*************
SQL Execution
*************

As the primary way a Python application communicates with Oracle Database , you can get pretty much the same experience on SQL statements execution as the original cx_Oracle library , with feature of bind variables supported as well. 

SQL Queries
===========

Both ``execute`` and ``executemany`` are supported.

.. code-block:: python

    import cx_Oracle_async
    import asyncio
    
    async def main():
        dsn = cx_Oracle_async.makedsn('localhost' , '1521' , service_name = 'orcl')
        pool = await cx_Oracle_async.create_pool('username', 'password', dsn)
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:

                # single fetch
                await cursor.execute("SELECT DNAME FROM SCOTT.DEPT WHERE DEPTNO = :a" , (10 , ))
                print(await cursor.fetchone())

                # multiple insert
                sql = "INSERT INTO SCOTT.DEPT(deptno , dname) VALUES (:a , :b)"
                sql_data = [
                    [60 , "Hello"],
                    [70 , "World"], 
                ]
                await cursor.executemany(sql , sql_data)
                await conn.commit()

                # multiple fetch
                await cursor.execute("SELECT * FROM SCOTT.DEPT WHERE DEPTNO < :maximum" , maximum = 100)
                print(await cursor.fetchall())

        await pool.close()

    asyncio.run(main())