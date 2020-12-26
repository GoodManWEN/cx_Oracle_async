import os , sys
o_path = os.getcwd()
sys.path.append(os.path.split(o_path)[0])
import pytest
import asyncio
from cx_Oracle_async import *

async def test_import():
    ...