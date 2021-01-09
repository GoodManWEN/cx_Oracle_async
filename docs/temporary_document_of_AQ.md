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
        await queue.enqOne() # clean
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