import collections
import asyncio
import numpy as np
from aiofsk.util import DoubleEvent


class FrameSynchronizer:
    def __init__(self, frame_size, receiving: DoubleEvent):
        self._frame_size = frame_size
        self.receiving = receiving
        self.unsynchronized_audio_in = asyncio.Queue()
        self.synchronized_audio_in = asyncio.Queue()

    async def synchronize(self):
        """
        Drop silence and compensate for misaligned audio frames
        """
        samples = collections.deque(maxlen=self._frame_size * 2)

        while True:
            if len(samples) < self._frame_size:
                sample = await self.unsynchronized_audio_in.get()
                samples.extend(sample.tolist())
                while len(samples) >= 2 and samples[0] == samples[1] == [0.0]:
                    samples.popleft()

            if len(samples) >= self._frame_size:
                self.receiving.set()
                window = np.ndarray((self._frame_size, 1))
                for i in range(self._frame_size):
                    sample = samples.popleft()
                    window[i] = sample
                self.synchronized_audio_in.put_nowait(window)
            else:
                self.receiving.clear()
