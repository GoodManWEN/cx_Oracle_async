class Counter:

    def __init__(self):
        self.success = 0
        self.fail = 0

async def single_thread_fetching(oracle_pool , counter):
    SQL = 'SELECT DEPTNO FROM "SCOTT"."DEPT" WHERE DEPTNO = 10'
    async with oracle_pool.acquire() as connection:
        async with connection.cursor() as cursor:
            while True:
                await cursor.execute(SQL)
                r = await cursor.fetchone()
                if r and r[0] == 10:
                    counter.success += 1
                else:
                    counter.fail += 1

async def report_thread(counter , oracle_pool):
    st_time =  time.time()
    while True:
        await asyncio.sleep(2)
        time_passed  = time.time() - st_time
        print(f"Report every 2 secs : [success] {counter.success} \t[fail] {counter.fail} \t[qps] {'%.2f' % round(counter.success / time_passed , 2)} \t[time_passed] {'%.2f' % round(time_passed,2)}s")

async def main():
    loop = asyncio.get_running_loop()
    oracle_pool = await cx_Oracle_async.create_pool( 
                                host='localhost', 
                                port='1521',
                                user='system', 
                                password='123456',
                                service_name='orcl', 
                                loop=loop,
                                min = 2,
                                max = THREAD_NUM,
                        )
    counter = Counter()
    loop = asyncio.get_running_loop()
    for _ in range(THREAD_NUM):
        loop.create_task(single_thread_fetching(oracle_pool , counter))
    loop.create_task(report_thread(counter , oracle_pool))
    while True:
        await asyncio.sleep(3600)

if __name__ == '__main__':
    import asyncio
    import cx_Oracle_async
    import time
    import os
    THREAD_NUM = (os.cpu_count() or 1) << 2
    asyncio.run(main())