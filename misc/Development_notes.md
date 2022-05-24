# Development notes

Due to insufficiencies in the conversion of the cx_oracle's native thread pool into coroutine threads and some problems in the use of the main branch of this repository. We have opened a development branch that is intended to take advantage of existing open source projects.

[SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) is a cool project. I mean, while it does have let people feel bloated at times, but overall it's still cool and has a far more sophisticated thread pool than our current solution. So we have made a simple demo that can support the basic CURD functions, using `SQLAlchemy` only to help us manage our thread pool without enabling its ORM functionality - sometimes it's better to leave the SQLs as they are.

The new version fixes several problems mentioned by the community in issues, and adds a better connection management facility, including automatic reconnection of disconnections caused by exceptions, etc. Unfortunately the current asynchronous events are still converted from the thread pool executor, as `cx_Oracle` currently is still the only way for python to connect to oracle database. However with `SQLAlchemy`'s background thread to help us deal with the logics, we have somewhat avoided the embarrassment of frequent commits to the executor as we did originally. The new version theoretically be more efficient in terms of thread utilization as the logic previously used for creating and destroying synchronized objects has been merged extensively.

If you want to install the development version, just clone the project and switch to the `dev` branch. Here is the code for the new version usage examples and feature demos. Despite they have not been tested in perfect detail, the logic is simple and thus should not lead to bugs. If the functions you need are not provided here, you may need to work on yourself.

```python
import cx_Oracle_async_sqlalchemy
import asyncio
try:
    import uvloop 
    uvloop.install()
except:
    ... 

async def task(oralce_pool, start_from: int):
    '''
    Parallel statements execution
    '''
    async with oralce_pool.acquire() as conn:
        await conn.execute_and_commit(
            'INSERT INTO SYSTEM.EMPLOYEE(id, department_id) VALUES (:a, 1)',
            [{'a': start_from+i} for i in range(10)]
        )

async def flooding(oralce_pool):
    '''
    Simulate instantaneous incoming large number of query requests
    '''
    async with oralce_pool.acquire() as conn:
        if conn.unavailable():
            print("Fail", end=', ')
            return 0
        print("Success", end=', ')
        await asyncio.sleep(1)
        await conn.select_one('SELECT * FROM SYSTEM.EMPLOYEE WHERE ROWNUM <= 1')
        return 1

async def main():

    oralce_pool = cx_Oracle_async_sqlalchemy.create_pool(
        host = 'localhost',
        port = 1521,
        sid = 'cdb1',
        user = 'system',
        password = '123456',
        pool_size = 5,
        max_overflow = 5,
        pool_timeout = 1,
        # https://docs.sqlalchemy.org/en/20/core/engines.html?highlight=pool_recycle#sqlalchemy.create_engine.params.pool_recycle
        pool_recycle = 3600,   
        # https://docs.sqlalchemy.org/en/20/core/engines.html?highlight=pool_use_lifo#sqlalchemy.create_engine.params.pool_use_lifo
        pool_use_lifo = True,
        # https://docs.sqlalchemy.org/en/20/core/engines.html?highlight=pool_pre_ping#sqlalchemy.create_engine.params.pool_pre_ping
        pool_pre_ping = True,
        echo = False,
        echo_pool = False
    )

    # Create a testing table
    async with oralce_pool.acquire() as conn:
        await conn.execute_and_commit('''
            CREATE TABLE SYSTEM.EMPLOYEE (
                id NUMBER(10, 0) NOT NULL,
                department_id NUMBER(10, 0) NOT NULL,
                PRIMARY KEY (id)
            )
        ''')    
    
    # Adding data in parallel
    await asyncio.gather(*[task(oralce_pool, x) for x in range(0,100,10)])

    # Basic queries
    # For ease of use, creating a cursor and fetching from the cursor are combined in a single call.
    async with oralce_pool.acquire() as conn:
        # It's worth noting that since the SQLAlchemy's Connection object we rely on is not thread-safe, 
        # this means that there are some limitations on how users can use it compared to normal asynchronous.
        # Concurrent requests are allowed, but you have to create an equal number of connections 
        # and cannot share the same Connection object between coroutines at a same time.
        r = await conn.select_one('SELECT * FROM SYSTEM.EMPLOYEE WHERE ROWNUM <= 1')
        print(r)

        r2 = await conn.select_all('SELECT * FROM SYSTEM.EMPLOYEE WHERE ROWNUM <= 10')
        print(r2)

    # Simulate instantaneous incoming large number of query requests
    r3 = await asyncio.gather(*[flooding(oralce_pool) for _ in range(1000)])
    
    # The thread pool has a buffering capability, and requests that are not executed immediately are cached and 
    # going to be executed later. However, there is an upper limit on the number of caches, currently set to 
    # about five times the maximum number of parallel load capacity, all requests exceeding this limit will be
    # rejected immediately.
    
    # Since acquiring a connection may fail for this reason, or for other reasons such as timeouts. So the user needs
    # to call `conn.unavailable()` to determine its availability when obtaining a connection for the first time.
    # This approach helps you to avoid setting try except on the upper layer of the context manager to prevent timeout events.
    print(f"\nTask returned immediately: {1000-sum(r3)}")
    
    # Destruction table
    async with oralce_pool.acquire() as conn:
        await conn.execute_and_commit('DROP TABLE SYSTEM.EMPLOYEE')
    
    # Close the connection pool and clear the connection. Note that this method does not force the terminating of 
    # a active connection.
    oracle_pool.close()
    await oracle_pool.wait_closed()

asyncio.run(main())
```
