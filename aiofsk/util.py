import asyncio


class DoubleEvent:
    def __init__(self):
        self._event = asyncio.Event()
        self._inverse = asyncio.Event()
        self._inverse.set()

    def set(self):
        self._inverse.clear()
        self._event.set()

    def is_set(self):
        return self._event.is_set()

    def clear(self):
        self._event.clear()
        self._inverse.set()

    def wait(self):
        return self._event.wait()

    def wait_clear(self):
        return self._inverse.wait()
