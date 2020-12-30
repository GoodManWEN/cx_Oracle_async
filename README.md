# cx_Oracle_async
[![fury](https://badge.fury.io/py/cx-Oracle-async.svg)](https://badge.fury.io/py/cx-Oracle-async)
[![licence](https://img.shields.io/github/license/GoodManWEN/cx_Oracle_async)](https://github.com/GoodManWEN/cx_Oracle_async/blob/master/LICENSE)
[![pyversions](https://img.shields.io/pypi/pyversions/cx-Oracle-async.svg)](https://pypi.org/project/cx-Oracle-async/)
[![Publish](https://github.com/GoodManWEN/cx_Oracle_async/workflows/Publish/badge.svg)](https://github.com/GoodManWEN/cx_Oracle_async/actions?query=workflow:Publish)
[![Build](https://github.com/GoodManWEN/cx_Oracle_async/workflows/Build/badge.svg)](https://github.com/GoodManWEN/cx_Oracle_async/actions?query=workflow:Build)

A very simple asynchronous wrapper that makes you can access to Oracle in asyncio programs.

Easy to use , buy may not the best practice for efficiency concern.

## Requirements
- [cx_Oracle >= 8.1.0](https://github.com/oracle/python-cx_Oracle) (Take into consideration that author of cx_Oracle said he's trying to implement asyncio support , APIs maybe change in future version. Switch to 8.1.0 if there's something wrong makes it not gonna work.)
- [ThreadPoolExecutorPlus >= 0.2.0](https://github.com/GoodManWEN/ThreadPoolExecutorPlus)

## Install

    pip install cx_Oracle_async
    
## Usage
- Nearly all the same with aiomysql (with very limited functions of cource)
- No automaticly date format transition built-in.

## Example
```Python3
# all_usages.py
import asyncio
import cx_Oracle_async

async def main():
    loop = asyncio.get_running_loop()
    oracle_pool = await cx_Oracle_async.create_pool(
        host='localhost', 
        port='1521',
        user='user', 
        password='password',
        db='orcl', 
        loop=loop,
        autocommit=False,  # this option has no use.
        minsize = 2,
        maxsize = 4,
    )

    async with oracle_pool.acquire() as connection:
        async with connection.cursor() as cursor:
            # single fetch 
            sql_1 = "SELECT * FROM SCOTT.DEPT WHERE deptno = :a"
            await cursor.execute(sql_1 , (10 , ))
            print(await cursor.fetchone())
            
            # multiple inert
            sql_2 = "INSERT INTO SCOTT.DEPT(deptno , dname) VALUES (:a , :b)"
            sql_2_data = [
                [60 , "Hello"],
                [70 , "World"], 
            ]
            await cursor.executemany(sql_2 , sql_2_data)
            await connection.commit()
            
            # multiple fetch
            sql_3 = "SELECT * FROM SCOTT.DEPT WHERE deptno >= :a"
            await cursor.execute(sql_3 , (60 , ))
            print(await cursor.fetchall())

if __name__ == '__main__':
    asyncio.run(main())
```
