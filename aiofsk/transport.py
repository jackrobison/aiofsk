import time
import queue
import asyncio
import threading
import contextlib
import numpy as np
import sounddevice as sd

from aiofsk.baud import DEFAULT_BAUD_OPTIONS
from aiofsk.modulation import MODULATORS
from aiofsk.util import DoubleEvent
from aiofsk.synchronizer import FrameSynchronizer


def audio_pipe(q_in, q_out, samplerate, blocksize, loopback=True):
    loop = asyncio.get_event_loop()

    def callback(indata, outdata, frame_count, time_info, status):

        try:
            # copy microphone input frame into incoming queue
            loop.call_soon_threadsafe(q_in.put_nowait, indata.copy())
        except RuntimeError:
            # raised if the loop stopped
            pass
        try:
            # put speaker output frame if one is ready
            outdata[:] = q_out.get_nowait()
        except queue.Empty:
            # otherwise fill silence
            outdata.fill(0)
        # if status:
        #     print(status)

    @contextlib.asynccontextmanager
    async def pipe_audio():
        with sd.Stream(device='default', channels=1, callback=callback,
                       samplerate=samplerate, blocksize=blocksize):
            yield

    @contextlib.asynccontextmanager
    async def loopback_audio():  # a mock sounddevice.Stream
        # attempt to replicate the real timing of the callback calls
        delay = 1 / (samplerate / blocksize)

        async def connect():
            silence = np.zeros((blocksize, 1))

            while True:
                await asyncio.sleep(delay)
                try:
                    outdata = q_out.get_nowait()
                except queue.Empty:
                    outdata = silence
                try:
                    loop.call_soon_threadsafe(q_in.put_nowait, outdata.copy())
                except RuntimeError:
                    pass

        connect_task = asyncio.create_task(connect())
        try:
            yield
        finally:
            if connect_task and not connect_task.done():
                connect_task.cancel()

    if loopback:
        return loopback_audio()
    return pipe_audio()


class AFSKTransport(asyncio.Transport):
    baud_rate_options = DEFAULT_BAUD_OPTIONS

    def __init__(self, baud: int = DEFAULT_BAUD_OPTIONS.default, loopback: bool = False, modulator: str = 'standard',
                 amplitude: float = 0.2):
        super().__init__()
        self.loopback = loopback
        self.baud_rate = self.baud_rate_options.make_baud_nt(baud)
        self.modulator = MODULATORS[modulator](self.baud_rate, amplitude)
        self._data_in: asyncio.Queue[bytes] = asyncio.Queue()
        self._data_out: asyncio.Queue[bytes] = asyncio.Queue()
        self._audio_out: queue.Queue[np.ndarray] = queue.Queue()

        self._stop = asyncio.Event()
        self._stop.set()
        self._stop_listen = threading.Event()
        self._stop_output = threading.Event()

        # initialize to 0
        self._audio_out.put(np.zeros((self.baud_rate.frame_size, 1), dtype='float32'))
        self.loop = asyncio.get_event_loop()
        self._receiving = DoubleEvent()
        self._sending = DoubleEvent()
        self.synchronizer = FrameSynchronizer(self.baud_rate.frame_size, self._receiving)
        self.connected = asyncio.Event()

    def stop(self):
        self._stop.set()

    def write(self, data: bytes):
        self._data_in.put_nowait(data)

    async def read(self, n: int, timeout=None) -> bytes:
        msg = b''
        start = time.perf_counter()

        for _ in range(n):
            if timeout:
                byte = await asyncio.wait_for(self._data_out.get(), timeout - (time.perf_counter() - start))
            else:
                byte = await self._data_out.get()
            msg += byte
        return msg

    async def _connect_audio(self):
        async with audio_pipe(
                self.synchronizer.unsynchronized_audio_in, self._audio_out, self.baud_rate.sample_rate,
                self.baud_rate.frame_size, loopback=self.loopback):
            await self._stop.wait()

    async def _connect(self):
        if self._stop.is_set():
            self._stop.clear()

        io_task = self.loop.create_task(self._connect_audio())
        sync_task = self.loop.create_task(self.synchronizer.synchronize())
        modulate_task = self.loop.create_task(self.modulator.modulate(self._data_in, self._audio_out))
        demodulate_task = self.loop.create_task(
            self.modulator.demodulate(self.synchronizer.synchronized_audio_in, self._data_out)
        )

        self.connected.set()
        try:
            await self._stop.wait()
        finally:
            self.connected.clear()
            self.loop.call_soon_threadsafe(self._stop_output.set)
            self.loop.call_soon_threadsafe(self._stop_listen.set)
            await asyncio.sleep(0)
            if not io_task.done():
                io_task.cancel()
            if not sync_task.done():
                sync_task.cancel()
            if not modulate_task.done():
                modulate_task.cancel()
            if not demodulate_task.done():
                demodulate_task.cancel()

    async def connect(self):
        self.loop.create_task(self._connect())
        await self.connected.wait()

    async def connect_and_run_forever(self):
        await self.connect()
        try:
            return await self._stop.wait()
        finally:
            self.stop()
