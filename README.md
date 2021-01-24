# cx_Oracle_async
[![fury](https://badge.fury.io/py/cx-Oracle-async.svg)](https://badge.fury.io/py/cx-Oracle-async)
[![licence](https://img.shields.io/github/license/GoodManWEN/cx_Oracle_async)](https://github.com/GoodManWEN/cx_Oracle_async/blob/master/LICENSE)
[![pyversions](https://img.shields.io/pypi/pyversions/cx-Oracle-async.svg)](https://pypi.org/project/cx-Oracle-async/)
[![Publish](https://github.com/GoodManWEN/cx_Oracle_async/workflows/Publish/badge.svg)](https://github.com/GoodManWEN/cx_Oracle_async/actions?query=workflow:Publish)
[![Build](https://github.com/GoodManWEN/cx_Oracle_async/workflows/Build/badge.svg)](https://github.com/GoodManWEN/cx_Oracle_async/actions?query=workflow:Build)

A very simple asynchronous wrapper that allows you to get access to the Oracle database in asyncio programs.

Easy to use , buy may not the best practice for efficiency concern.

## Requirements
- [cx_Oracle >= 8.1.0](https://github.com/oracle/python-cx_Oracle) (Take into consideration that author of cx_Oracle said he's trying to implement asyncio support , APIs maybe change in future version. Switch to 8.1.0 if there's something wrong makes it not gonna work.)
- [ThreadPoolExecutorPlus >= 0.2.0](https://github.com/GoodManWEN/ThreadPoolExecutorPlus)

## Install

    pip install cx_Oracle_async
    
## Usage
- Nearly all the same as aiomysql in asynchronous operational approach , with limited cx_Oracle feature support.
- No automaticly date format transition built-in.
- AQ feature added , check [docs here](https://github.com/GoodManWEN/cx_Oracle_async/blob/main/docs/temporary_document_of_AQ.md) for further information.
- You can modify some of the connection properties simply like you're using cx_Oracle. 
- You can do basic insert / select / delete etc.
- If you're connecting to database which is on a different machine from python process , you need to install oracle client module in order to use this library. Check [cx-Oracle's installation guide](https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html) for further information.

## Performance
query type | asynchronous multithreading | synchronous multithreading | synchronous single thread
-|-|-|-
fast single line query | 6259.80 q/s | 28906.93 q/s | 14805.61 q/s
single line insertion | 1341.88 q/s | 1898 q/s | 1685.17 q/s

*/\* Test platform: \*/*<br>
*AMD Ryzen 3700x*<br>
*Windows 10 LTSC*<br>
*Oracle 19c*<br>
*You can find performance test codes [here](https://github.com/GoodManWEN/cx_Oracle_async/blob/main/misc).*

## Examples
Before running examples , make sure you've already installed a [oracle client](https://github.com/GoodManWEN/cx_Oracle_async#usage) on your machine.
```Python
# basic_usages.py
import asyncio
import cx_Oracle_async

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

    await oracle_pool.close()

if __name__ == '__main__':
    asyncio.run(main())
```

Or you can connect to database via dsn style:
```Python
# makedsn.py
import asyncio
import cx_Oracle_async

async def main():
    # same api as cx_Oracle.makedsn with 4 limited parameters(host , port , sid , service_name).
    dsn = cx_Oracle_async.makedsn(host = 'localhost' , port = '1521' , service_name = 'orcl')
    async with cx_Oracle_async.create_pool(user='', password='',dsn = dsn) as pool:
        ...

asyncio.run(main())
```
