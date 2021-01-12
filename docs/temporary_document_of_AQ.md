# Temporary document of AQ

We made a very simple implement of [Advanced Queue](https://cx-oracle.readthedocs.io/en/latest/user_guide/aq.html#oracle-advanced-queuing-aq) as it's Oracledb's exclusive feature. Here's a rough draft with basic examples shows you how to use it .

## Examples

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

        # Syntactic sugar
        # There re some equivalent replacements Perticularly in this async library for convenient use.
        queue = await conn.queue("DEMO_RAW_QUEUE")
        async for _ in queue.deqMany():... # Clear queue
        message = "Hello World"
        
        # Queue.pack(m) is equal to Connection.msgproperties(payload=m) 
        await queue.enqOne(queue.pack(message)) 
        await queue.enqOne(conn.msgproperties(payload=message)) 
        await conn.commit()

        # Queue.unpack(m) is equal to m.payload.decode(conn.encoding)
        ret1 = queue.unpack(await queue.deqOne())
        ret2 = (await queue.deqOne()).payload.decode(conn.encoding)
        await conn.commit()
        assert ret1 == ret2 == message

        # Queue.unpack(m) will do automatically treatment depends on whether input a single object or a iterable.
        await queue.enqMany(queue.pack(m) for m in map(str , range(10)))
        await conn.commit()
        ret1 = queue.unpack(await queue.deqMany())  # This returns a list but not a single object.
        await conn.commit()

        ret2 = []
        await queue.enqMany(queue.pack(m) for m in map(str , range(10)))
        await conn.commit()
        async for m in queue.deqMany():
            ret2.append(queue.unpack(m))  # This returns a single object since one input eachtime.
        assert ret1 == ret2

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
    async with cx_Oracle_async.create_pool(user = '' , password = '' , dsn = dsn) as oracle_pool:
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
    async with cx_Oracle_async.create_pool(user = '' , password = '' , dsn = dsn) as oracle_pool:
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

## Special Explanation for queue.deqMany()

Queue.deqMany has a little bit complexity in usage , here're some further instructions.
```Python
import cx_Oracle_async
import asyncio
import random

async def main():
    loop = asyncio.get_running_loop()
    dsn = cx_Oracle_async.makedsn(
        host = 'localhost',
        port = '1521',
        service_name='orcl'
    )
    async with cx_Oracle_async.create_pool(user = '' , password = '' , dsn = dsn) as oracle_pool:
        async with oracle_pool.acquire() as conn:

            # Init and clear a queue
            queue = await conn.queue("DEMO_RAW_QUEUE")
            async for _ in queue.deqMany():...

            # There're two ways of calling deqMany , you can use it as a normal asynchronous call , 
            # OR you can use it as a asynchronous generator.
            # For example.

            await queue.enqMany(queue.pack(m) for m in map(str , range(10)))
            await conn.commit()

            # The First way , use it as a normal asynchronous call , 
            # This method use the original cx_Oracle.Queue.deqMany , so its
            # your choice if you're looking for efficiency concern. The
            # sub thread will block until all results returned.
            
            ret = await queue.deqMany(maxMessages = 10)
            await conn.commit()
            assert list(map(queue.unpack , ret)) == list(map(str , range(10)))

            # The second way , you can call deqMany as a asynchronous generator.
            # This is a self implemented method which yield queue.deqMany() with
            # queue.deqOptions = DEQ_NO_WAIT until it reaches the message limit or
            # there's nothing in the queue. The benifits is you will get immediate 
            # response. 

            await queue.enqMany(queue.pack(m) for m in map(str , range(10)))
            await conn.commit()

            ret = []
            async for m in queue.deqMany(maxMessages = 10):
                ret.append(queue.unpack(m))
            await conn.commit()
            assert ret == list(map(str , range(10)))
            
            # It is worth mentioning that , the two means act differently
            # when there's a empty queue.

            # If you are using the `await` mode , for example `ret == await queue.deqMany()`
            # if there's do have something in the queue , this method will quickly return , 
            # while if there's nothing in the queue , the method will block until there's 
            # something new come into the queue , this sometime will make it a deadlock 
            # in main threadloop under improper use. So do please make sure you're clear about
            # what you're doing.

            # Of course you can change deqOptions into non-blocking mode like
            # `queue.deqOptions.wait = cx_Oracle_async.DEQ_NO_WAIT` to aviod it.

            # On the other hand ,  If you are using the `async with` mode , it will  
            # never block your main thread , however it will not be affected by 
            # `Queue.deqOptions` , no matter what setting `Queue.deqOptions` is , 
            # it will return immediately when there's nothing in the queue.
 
            # So taking into consideration that when argument maxMessages equals to 
            # -1 (default value), it means unlimit fetch untill the queue is empty. 
            # It's convenient to clear the whole queue with the following code:

            messages = list(map(str , range(random.randint(0,10000))))
            await queue.enqMany(queue.pack(m) for m in messages)
            await conn.commit()

            # You are not clear about how large the queue size is (there's also chance it's empty)
            # and want to take out all stuffs in it if its not empty.
            ret = []
            async for m in queue.deqMany():
                ret.append(queue.unpack(m))
            print(ret)

            # Do something keep on.
            ...


asyncio.run(main())
```