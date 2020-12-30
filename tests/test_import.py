import os , sys
sys.path.append(os.getcwd())
import pytest
import asyncio
from cx_Oracle_async import *

@pytest.mark.asyncio
async def test_import():
    ...
