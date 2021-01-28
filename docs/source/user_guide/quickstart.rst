.. _quickstart:

***********
Quick Start
***********

Install cx_Oracle_async
=======================

Supports python3.7 or later.

- Install from PyPI:

.. code-block:: 

    pip instal cx_Oracle_async

Install Oracle Client
=====================

If you're connecting to database which is on a different machine from python process , you need to setup a oracle instanct client module in order before you use this library. Check \ `cx-Oracle's installation guide <https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html#overview>`_ for further information.

Basic Usage
===========

All usage in **cx_Oracle_async** based on the session pool,  **cx_Oracle_async** does not provide means you can setup a simple connection to database without pool manager.

Here's a basic example:

.. code-block:: python
    
    import cx_Oracle_async
    import asyncio

    async def main():
        oracle_pool = await cx_Oracle_async.create_pool(
            host='localhost', 
            port='1521',
            user='user', 
            password='password',
            service_name='orcl', 
            min = 2,
            max = 4,
        )

        async with oracle_pool.acquire() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT * FROM V$SESSION")
                print(await cursor.fetchall())
    
        await oracle_pool.close()
    
    asyncio.run(main())

Or you may prefer to use ``makedsn`` style to manage your token and server destinations:

.. code-block:: python
    
    async def main():
        dsn = cx_Oracle_async.makedsn('localhost' , '1521' , service_name = 'orcl')
        oracle_pool = await cx_Oracle_async.create_pool(
            'username' , 
            'password' , 
            dsn,
        )
        ...

You can use both context manager / non-context manager way to access your :meth:`SessionPool` , :meth:`Connection` , :meth:`Cursor` object , they will act the same in results.

.. code-block:: python
    
    from cx_Oracle_async import makedsn , create_pool
    import asyncio

    async def main():
        dsn = makedsn('localhost' , '1521' , service_name = 'orcl')
        pool_1 = await create_pool('username' , 'password' , dsn)
        
        async with create_pool('username' , 'password' , dsn) as pool_2:
            assert type(pool_1) == type(pool_2)

            conn_1 = await pool_2.acquire()
            async with pool_2.acquire() as conn_2:
                assert type(conn_1) == type(conn_2)

                cursor = await conn.cursor()
                await cursor.execute("SELECT * FROM V$SESSION")

        await pool_1.close()
    
    asyncio.run(main())

Closing SessionPools
--------------------

You can hardly run into close problem in normal use with the help of a context manager , however , if you're using some kind of nested code structure , ``SessionPool.close()`` may get ``cx_Oracle.DatabaseError: ORA-24422`` which indicates there's still some connection remaining activate when ``close`` triggered. In this perticular situation , you may need to use ``SessionPool.close(force = True)`` to ignore those error.

.. code-block:: python

    import cx_Oracle_async
    import asyncio

    async def solitary_fetching_thread(pool):
        # Simulation of a long duration query.
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("BEGIN DBMS_LOCK.SLEEP(10); END;")
    
    async def main():
        dsn = cx_Oracle_async.makedsn('localhost' , '1521' , service_name = 'orcl')
        pool = await cx_Oracle_async.create_pool(
            'username' , 
            'password' , 
            dsn,
        )
        
        loop = asyncio.get_running_loop()
        loop.create_task(solitary_fetching_thread(pool))

        await asyncio.sleep(2)
        # If you're not using force == True (which is False by default)
        # you'll get a exception of ORA-24422.
        await pool.close(force = True)

    asyncio.run(main())

It is noteworthy that although ``force = True`` is set , main thread loop of ``pool.close()`` will not continue untill all connection finished its query anyhow. In latest version of Oracle database (e.g. Oracle DB 19c) , you can use ``interrupt = True`` to let every activate connection in sessionpool cancel its current qurey in order to get a quick return. However , **DO NOT** use this feature if you're using a legacy version of Orace DB such as Oracle DB 11g , force cancel feature may cause connection no response and create a deadlock in your mainloop.

.. code-block:: python

    import cx_Oracle_async
    import asyncio
    from async_timeout import timeout

    async def solitary_fetching_thread(pool):
        # Simulation of a long duration query.
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute("BEGIN DBMS_LOCK.SLEEP(10); END;")
    
    async def main():
        dsn = cx_Oracle_async.makedsn('localhost' , '1521' , service_name = 'orcl')
        pool = await cx_Oracle_async.create_pool(
            'username' , 
            'password' , 
            dsn,
        )
        
        loop = asyncio.get_running_loop()
        loop.create_task(solitary_fetching_thread(pool))

        await asyncio.sleep(2)
        async with timeout(2):
            # This will not cause a asyncio.TimeoutError exception
            # cause the long duration query is canceled.
            await pool.close(force = True , interrupt = True)

    asyncio.run(main())