import numpy as np
from aiofsk.synchronizer import FrameSynchronizer
from aiofsk.util import DoubleEvent
from tests import AsyncioTestCase


class TestFrameSynchronizer(AsyncioTestCase):
    async def _test_sync_frames(self, zero_pad=0):
        frame_size = 48000 // 300
        receiving = DoubleEvent()
        synchronizer = FrameSynchronizer(frame_size, receiving)
        sync_task = self.loop.create_task(synchronizer.synchronize())
        self.addCleanup(sync_task.cancel)
        frames = [
            np.zeros((frame_size, 1)),
            np.zeros((frame_size, 1)),
            np.zeros((frame_size, 1)),
            np.zeros((frame_size, 1))
        ]
        data = ([0.0] * zero_pad) + [0.0] + ([1.0] * (frame_size - 1)) + [0.0] + ([1.0] * (frame_size - 1))
        data_idx = 0
        for frame in frames:
            for i in range(len(frame)):
                if data_idx < len(data):
                    frame[i][0] = data[data_idx]
                    data_idx += 1
        expected = [0.0] + ([1.0] * (frame_size - 1))
        for frame in frames:
            synchronizer.unsynchronized_audio_in.put_nowait(frame)
        sync1 = await synchronizer.synchronized_audio_in.get()
        self.assertListEqual(expected, [i[0] for i in sync1])
        sync2 = await synchronizer.synchronized_audio_in.get()
        self.assertListEqual(expected, [i[0] for i in sync2])

    async def test_sync_frames_zero_offset(self):
        return await self._test_sync_frames(0)

    async def test_sync_frames_1_offset(self):
        return await self._test_sync_frames(1)

    async def test_sync_frames_25_offset(self):
        return await self._test_sync_frames(25)

    async def test_sync_frames_101_offset(self):
        return await self._test_sync_frames(101)

    async def test_sync_frames_140_offset(self):
        return await self._test_sync_frames(140)

    async def test_sync_frames_165_offset(self):
        return await self._test_sync_frames(165)
