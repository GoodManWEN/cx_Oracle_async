from concurrent.futures import ThreadPoolExecutor
import cx_Oracle
import os
import time

class Counter:

    def __init__(self , num):
        self.success = [0 for _ in range(num)]
        self.fail = [0 for _ in range(num)]

def single_thread(pool , counter , _id):
    SQL = "SELECT DEPTNO FROM SCOTT.DEPT WHERE DEPTNO = 10"
    connection = pool.acquire()
    cursor = connection.cursor()
    while True:
        cursor.execute(SQL)
        r = cursor.fetchone()
        if r and r[0] == 10:
            counter.success[_id] += 1
        else:
            counter.fail[_id] += 1
        # break

THREAD_NUM = (os.cpu_count() or 1) << 1
pool = cx_Oracle.SessionPool("system", "123456", "localhost:1521/orcl" , min =1 , max = 4 , increment = 1 , threaded = True , encoding = 'UTF-8')
counter = Counter(THREAD_NUM)
with ThreadPoolExecutor(max_workers = THREAD_NUM << 5) as executor:
    for _ in range(THREAD_NUM):
        executor.submit(single_thread , pool , counter , _)
    st_time = time.time()
    while True:
        time.sleep(2)
        time_passed = time.time() - st_time
        print(f"Report every 2 secs : [success] {sum(counter.success)} \t[fail] {sum(counter.fail)} \t[qps] {'%.2f' % round(sum(counter.success) / time_passed , 2)} \t[time_passed] {'%.2f' % round(time_passed,2)}s")