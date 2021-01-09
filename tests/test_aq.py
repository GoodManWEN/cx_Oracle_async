import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
import time
from cx_Oracle_async import *
import cx_Oracle

async def modify_deqopts(queue , val):
    queue.deqOptions.wait = val

async def fetch_from_queue_no_wait(oracle_pool , loop):
    async with oracle_pool.acquire() as conn:
        queue = await conn.queue("DEMO_RAW_QUEUE")
        loop.create_task(modify_deqopts(queue , cx_Oracle.DEQ_NO_WAIT))
        ret = await queue.deqOne()
        if ret:
            ret = ret.payload.decode(conn.encoding)
        await conn.commit()
        return ret

async def fetch_from_queue_wait_forever(oracle_pool , loop):
    async with oracle_pool.acquire() as conn:
        queue = await conn.queue("DEMO_RAW_QUEUE")
        loop.create_task(modify_deqopts(queue , cx_Oracle.DEQ_WAIT_FOREVER))
        ret = await queue.deqOne()
        if ret:
            ret = ret.payload.decode(conn.encoding)
        return ret

async def put_into_queue(oracle_pool , loop):
    await asyncio.sleep(2)
    async with oracle_pool.acquire() as conn:
        queue = await conn.queue("DEMO_RAW_QUEUE")
        await queue.enqOne(conn.msgproperties(payload='Hello World'))
        await conn.commit()

@pytest.mark.asyncio
async def test_multiquery():
    loop = asyncio.get_running_loop()
    dsn  = makedsn('localhost','1521',sid='xe')
    INAQ = 0.5
    async with create_pool(user='system',password='oracle',dsn=dsn,max=4) as oracle_pool:
        async with oracle_pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute("""
                        BEGIN
                          DBMS_AQADM.STOP_QUEUE(queue_name => 'DEMO_RAW_QUEUE');
                          DBMS_AQADM.DROP_QUEUE(queue_name => 'DEMO_RAW_QUEUE');
                          DBMS_AQADM.DROP_QUEUE_TABLE(queue_table => 'MY_QUEUE_TABLE');
                        END;

                    """)
                except Exception as e:
                    ...

                await cursor.execute("""
                        BEGIN
                            DBMS_AQADM.CREATE_QUEUE_TABLE('MY_QUEUE_TABLE', 'RAW');
                            DBMS_AQADM.CREATE_QUEUE('DEMO_RAW_QUEUE', 'MY_QUEUE_TABLE');
                            DBMS_AQADM.START_QUEUE('DEMO_RAW_QUEUE');
                        END;
                    """)

                try:
                    await cursor.execute("DROP TYPE udt_book FORCE")
                except Exception as e:
                    ...

                await cursor.execute("""
                    CREATE OR REPLACE TYPE udt_book AS OBJECT (
                        Title   VARCHAR2(100),
                        Authors VARCHAR2(100),
                        Price   NUMBER(5,2)
                    );
                    """)

                try:
                    await cursor.execute("""
                        BEGIN
                          DBMS_AQADM.STOP_QUEUE(queue_name => 'DEMO_BOOK_QUEUE2');
                          DBMS_AQADM.DROP_QUEUE(queue_name => 'DEMO_BOOK_QUEUE2');
                          DBMS_AQADM.DROP_QUEUE_TABLE(queue_table => 'BOOK_QUEUE_TAB2');
                        END;

                    """)
                except Exception as e:
                    ...

                await cursor.execute("""
                        BEGIN
                            DBMS_AQADM.CREATE_QUEUE_TABLE('BOOK_QUEUE_TAB2', 'UDT_BOOK');
                            DBMS_AQADM.CREATE_QUEUE('DEMO_BOOK_QUEUE2', 'BOOK_QUEUE_TAB2');
                            DBMS_AQADM.START_QUEUE('DEMO_BOOK_QUEUE2');
                        END;
                    """)

                # test put
                queue = await conn.queue("DEMO_RAW_QUEUE")
                PAYLOAD_DATA = [
                    "The first message",
                    "The second message",
                ]
                for data in PAYLOAD_DATA:
                    await queue.enqOne(conn.msgproperties(payload=data))
                await conn.commit()

                # test get
                queue = await conn.queue("DEMO_RAW_QUEUE")
                msg = await queue.deqOne()
                assert msg.payload.decode(conn.encoding) == "The first message"
                msg = await queue.deqOne()
                assert msg.payload.decode(conn.encoding) == "The second message"
                await conn.commit()

                # Define your own type of data
                booksType = await conn.gettype("UDT_BOOK")
                book = booksType.newobject()
                book.TITLE = "Quick Brown Fox"
                book.AUTHORS = "The Dog"
                book.PRICE = 123

                # Put and get modified data
                queue = await conn.queue("DEMO_BOOK_QUEUE2", booksType)
                await queue.enqOne(conn.msgproperties(payload=book))
                await conn.commit()
                msg = await queue.deqOne()
                await conn.commit()
                assert msg.payload.TITLE == "Quick Brown Fox"

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
                res = []
                async for m in queue.deqMany(maxMessages=5):
                    res.append(m.payload.decode(conn.encoding))
                await queue.deqOne() # clean
                await conn.commit()
                assert res == list(map(str,range(1,6)))

                # Get nowait
                st_time = time.time()
                async for m in queue.deqMany(maxMessages=5):
                    res.append(m.payload.decode(conn.encoding))
                ed_time = time.time()
                assert (ed_time - st_time) <= 0.5

        # test aq options
        st_time = time.time()
        _task = loop.create_task(fetch_from_queue_no_wait(oracle_pool , loop))
        result = await _task
        ed_time = time.time()
        assert result == None
        assert (ed_time - st_time) <= INAQ

        #
        st_time = time.time()
        _task = loop.create_task(fetch_from_queue_wait_forever(oracle_pool , loop))
        loop.create_task(put_into_queue(oracle_pool , loop))
        result = await _task
        ed_time = time.time()
        assert result == "Hello World"
        assert (2 - INAQ) <= (ed_time - st_time) <= (2 + INAQ)