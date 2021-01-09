# Temporary document of AQ

We made a very simple implement of [Advanced Queue](https://cx-oracle.readthedocs.io/en/latest/user_guide/aq.html#oracle-advanced-queuing-aq) as it's Oracledb's exclusive feature. Here's a rough draft with basic examples shows you how to use it .

## Example

Before running python codes below , you need to create queues in the database via console mode ,use tools such as SQL\*Plus , run the following SQL:

```
-- Create a queue for basic test
BEGIN
    DBMS_AQADM.CREATE_QUEUE_TABLE('MY_QUEUE_TABLE', 'RAW');
    DBMS_AQADM.CREATE_QUEUE('DEMO_RAW_QUEUE', 'MY_QUEUE_TABLE');
    DBMS_AQADM.START_QUEUE('DEMO_RAW_QUEUE');
END;

-- Create your own data type
CREATE OR REPLACE TYPE udt_book AS OBJECT (
    Title   VARCHAR2(100),
    Authors VARCHAR2(100),
    Price   NUMBER(5,2)
);

-- Create a queue to contain modified data type.
BEGIN
    DBMS_AQADM.CREATE_QUEUE_TABLE('BOOK_QUEUE_TAB', 'UDT_BOOK');
    DBMS_AQADM.CREATE_QUEUE('DEMO_BOOK_QUEUE', 'BOOK_QUEUE_TAB');
    DBMS_AQADM.START_QUEUE('DEMO_BOOK_QUEUE');
END;
```

Then you can get access to AQ through the following code, all features included:
```Python
import cx_Oracle_async
import asyncio

async def features(oracle_pool):
    async with oracle_pool.acquire() as conn:
        # Basic put
        queue = await conn.queue("DEMO_RAW_QUEUE")
        PAYLOAD_DATA = [
            "The first message",
            "The second message",
            "The third message"
        ]
        for data in PAYLOAD_DATA:
            await queue.enqOne(conn.msgproperties(payload=data))
        await conn.commit()

        # Basic get
        queue = await conn.queue("DEMO_RAW_QUEUE")
        for _ in range(len(PAYLOAD_DATA)):
            msg = await queue.deqOne()
        print(msg.payload.decode(conn.encoding))
        await conn.commit()

        # Define your own type of data
        booksType = await conn.gettype("UDT_BOOK")
        book = booksType.newobject()
        book.TITLE = "Quick Brown Fox"
        book.AUTHORS = "The Dog"
        book.PRICE = 123

        # Put and get modified data
        queue = await conn.queue("DEMO_BOOK_QUEUE", booksType)
        await queue.enqOne(conn.msgproperties(payload=book))
        msg = await queue.deqOne()
        print(msg.payload.TITLE)
        await conn.commit()
        
        # Put many
        messages = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6"
        ]
        queue = await conn.queue("DEMO_RAW_QUEUE")
        await queue.enqMany(conn.msgproperties(payload=m) for m in messages)
        await conn.commit()

        # Get many
        async for m in queue.deqMany(maxMessages=5):
            print(m.payload.decode(conn.encoding))
        await queue.deqOne() # clean
        await conn.commit()


async def main():
    dsn = cx_Oracle_async.makedsn(
        host = 'localhost',
        port = '1521',
        service_name='orcl'
    )
    async with cx_Oracle_async.create_pool(user = '' , password = '' , dsn = dsn) as oracle_pool:
        await features(oracle_pool)

asyncio.run(main())
```

It is noteworthy that since we were not implement this library asynchronous in a very basic level ,yet it's just a wrapper of synchronous functions via threads , that makes it not gonna work if you are doing two different things in a single connection at a time. For example in the following situation the code will **NOT** work:

```Python
import cx_Oracle_async
import asyncio

async def coro_to_get_from_queue(conn , queue , oracle_pool):
    print(f"coroutine start fetching")
    ret = (await queue.deqOne()).payload.decode(conn.encoding)
    print(f"coroutine returned , {ret=}")
    await conn.commit()

async def main():
    loop = asyncio.get_running_loop()
    dsn = cx_Oracle_async.makedsn(
        host = 'localhost',
        port = '1521',
        service_name='orcl'
    )
    async with cx_Oracle_async.create_pool(user = 'C##SCOTT' , password = '123456' , dsn = dsn) as oracle_pool:
        async with oracle_pool.acquire() as conn:
            queue = await conn.queue("DEMO_RAW_QUEUE")
            loop.create_task(coro_to_get_from_queue(conn , queue , oracle_pool))

            await asyncio.sleep(1)
            
            data = 'Hello World'
            print(f"mainthread put some thing in queue ,{data=}")
            await queue.enqOne(conn.msgproperties(payload=data))
            await conn.commit()
            print(f"mainthread put some thing done")

    await asyncio.sleep(1)
    print('Process terminated.')

asyncio.run(main())
```

As we planned , there should be a fetching thread(coroutine) start fetcing , this action will block since the queue is empty , and will return until there's something put into the queue. Then after one second sleep , the main thread will put 'Hello World' into AQ and that will trigger the blocked fetching thread , and then the whole program terminated.

However we will find the program blocking forever in real practice. That's because since `queue.deqOptions.wait` equals to `cx_Oracle.DEQ_WAIT_FOREVER` thus while there's nothing in the queue , the query will block **AND** this will take over the control of connection thread , which makes it impossible for the following code to put anything into the queue using the same thread, thus makes it a deadlock.

If you would like to achieve the same result , you should do that in **ANOTHER** connection thread. Simply modify the code as follow:
```Python
import cx_Oracle_async
import asyncio
from async_timeout import timeout

async def coro_to_get_from_queue(conn , queue , oracle_pool):
    try:
        async with timeout(2):
            print(f"coroutine start fetching")
            ret = (await queue.deqOne()).payload.decode(conn.encoding)
            print(f"coroutine returned , {ret=}")
            await conn.commit()
    except asyncio.TimeoutError:
        print('two seconds passed , timeout triggered.')
        async with oracle_pool.acquire() as conn2:
            queue2 = await conn2.queue("DEMO_RAW_QUEUE")
            data = 'Hello World'
            print(f"another connection put some thing in queue ,{data=}")
            await queue2.enqOne(conn2.msgproperties(payload=data))
            await conn2.commit()
            print(f"another connection put some thing done")

async def main():
    loop = asyncio.get_running_loop()
    dsn = cx_Oracle_async.makedsn(
        host = 'localhost',
        port = '1521',
        service_name='orcl'
    )
    async with cx_Oracle_async.create_pool(user = 'C##SCOTT' , password = '123456' , dsn = dsn) as oracle_pool:
        async with oracle_pool.acquire() as conn:
            queue = await conn.queue("DEMO_RAW_QUEUE")
            loop.create_task(coro_to_get_from_queue(conn , queue , oracle_pool))

            await asyncio.sleep(1)

            cursor = await conn.cursor()
            await cursor.execute(f"SELECT COUNT(*) FROM DEPT")
            fetch_result = await cursor.fetchall()
            print(f"main thread continue , {fetch_result=}")

    await asyncio.sleep(1)
    print('Process terminated.')

asyncio.run(main())
```