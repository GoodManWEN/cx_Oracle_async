from types import CoroutineType

class AbstractContextManager:

    def __init__(self , coro : CoroutineType):
        self._coro = coro
        self._obj = None

    # def __next__(self):
    #     return self.send(None)

    def __iter__(self):
        return self._coro.__await__()

    def __await__(self):
        return self._coro.__await__()

    async def __aenter__(self):
        self._obj = await self._coro
        return self._obj

    async def __aexit__(self, exc_type, exc, tb):
        ...