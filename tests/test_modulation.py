import numpy as np
import matplotlib.pyplot as plt
from aiofsk.modulation import Modulator
from aiofsk.transport import AFSKTransport
from aiofsk.file import write_wav, read_wav
from tests import AsyncioTestCase


class ModulationTests(AsyncioTestCase):
    async def test_derp(self):
        modulator = Modulator(AFSKTransport.baud_rate_options.make_baud_nt(300))
        data = np.zeros((modulator.frame_size * 8, 1))
        idx = 0
        for b in ['0', '1', '0', '0', '0', '0', '0', '1']:
            # ts += 1
            modulated = modulator.modulate_bit(b)
            print("modulated", len(modulated))
            for i in modulated:
                data[idx] = i
                idx += 1
        for i, x in enumerate(data):
            if x[0] == 0:
                print(i)
        plt.plot(data)
        plt.show()

    # async def test_encode_decode(self):
    #     tmp_dir = tempfile.mkdtemp()
    #     self.addCleanup(lambda: shutil.rmtree(tmp_dir))
    #     wav_path = os.path.join(tmp_dir, 'test.wav')
    #     modulator = Modulator(
    #         AFSKTransport.baud_rate_options.make_baud_nt(300), {'0': 1200, '1': 2400}
    #     )
    #     frames = np.zeros((modulator.frame_size * 8, 1))
    #     i = 0
    #     bits = ['0', '1', '0', '0', '0', '0', '0', '1']
    #     for b in bits:
    #         modulated = modulator.modulate_bit(b, 0)
    #         for sample in modulated:
    #             frames[i] = sample
    #             i += 1
    #     scipy.io.wavfile.write(wav_path, 48000, frames)
    #     rate, data = scipy.io.wavfile.read(wav_path)
    #     self.assertEqual(len(data), len(frames))
    #     self.assertEqual(rate, modulator.sample_rate)
    #     demodulated_bits = []
    #     for idx in range(0, len(frames), modulator.frame_size):
    #         demodulated_frame = np.zeros((modulator.frame_size, 1))
    #         for i in range(modulator.frame_size):
    #             demodulated_frame[i][0] = data[idx + i]
    #         with modulator.get_demodulation_context(0) as demodulate:
    #             demodulated_bits.append(str(demodulate(demodulated_frame)))
    #     self.assertListEqual(bits, demodulated_bits)

    async def _test_encode_decode(self, baud, modulator, msg=b'derp'):
        transport = AFSKTransport(baud, loopback=True, modulator=modulator)
        await transport.connect()
        self.addCleanup(transport.stop)
        transport.write(msg)
        demodulated = await transport.read(len(msg), timeout=0.25)
        self.assertEqual(msg, demodulated)

    async def test_encode_decode_300_baud_standard(self):
        await self._test_encode_decode(300, 'standard')

    async def test_encode_decode_1200_baud_standard(self):
        await self._test_encode_decode(1200, 'standard', b'\xffderp')

    async def test_encode_decode_300_baud_nrzi(self):
        await self._test_encode_decode(300, 'nrzi')

    async def test_encode_decode_1200_baud_nrzi(self):
        await self._test_encode_decode(1200, 'nrzi', b'\xffderp')

    async def _test_read_write_wave(self, msg=b'derp', baud=300):
        await write_wav('derp.wav', msg, baud=baud)
        self.assertEqual(msg, await read_wav('derp.wav', baud=baud))

    async def test_read_write_wave(self):
        return await self._test_read_write_wave(b'hello jake')
