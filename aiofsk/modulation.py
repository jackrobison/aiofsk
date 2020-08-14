import typing
import contextlib
import asyncio
import queue
import numpy as np
from aiofsk.baud import BaudRate, TONES


def frequency_counter(wave, sample_rate):
    was_positive = True
    period = 0
    for i in wave:
        positive = i[0] > 0
        if (positive and was_positive) or (not positive and not was_positive):
            pass
        elif positive:
            period += 1
        was_positive = positive
    return int(period / (len(wave) / sample_rate))


class Modulator:
    tones = TONES
    reverse_tones = {frequency: symbol for symbol, frequency in tones.items()}

    def __init__(self, baud: BaudRate, amplitude=1.0):
        self._baud = baud
        self._amplitude = amplitude
        self._base_frame = np.arange(self._baud.frame_size)
        self.demodulated = asyncio.Queue()

    @property
    def frame_size(self):
        return self._baud.frame_size

    @property
    def sample_rate(self):
        return self._baud.sample_rate

    @contextlib.contextmanager
    def get_encoder(self):
        def encode(bit: str) -> str:
            return bit

        yield encode

    @contextlib.contextmanager
    def get_decoder(self):
        def decode(bit: bool) -> int:
            if bit:
                return 1
            return 0

        yield decode

    def modulate_bit(self, symbol: str) -> np.array:
        tone = self.tones[symbol]
        return self._amplitude * np.cos(
            2 * np.pi * tone * (self._base_frame / self.sample_rate).reshape(-1, 1)
        )

    @staticmethod
    def iter_symbols(char):
        for bit in range(7, -1, -1):
            yield str((char >> bit) % 2)

    @contextlib.contextmanager
    def get_modulation_context(self):
        with self.get_encoder() as encode:
            def modulate_byte(char):
                for symbol in self.iter_symbols(char):
                    frame = self.modulate_bit(encode(symbol))
                    yield frame
            yield modulate_byte

    @contextlib.contextmanager
    def get_demodulation_context(self) -> typing.ContextManager[typing.Callable[[np.ndarray], str]]:
        with self.get_decoder() as decode:
            zero_mask = tuple([i[0] for i in self.modulate_bit('0')])
            one_mask = tuple([i[0] for i in self.modulate_bit('1')])

            def demodulate_bit(frame):
                zero_diff = sum(abs(a - b[0]) for (a, b) in zip(zero_mask, frame))
                one_diff = sum(abs(a - b[0]) for (a, b) in zip(one_mask, frame))
                bit = decode(one_diff < zero_diff)
                # print(frequency_counter(frame, self.sample_rate), bit)
                return bit

            yield demodulate_bit

    async def modulate(self, data_in: asyncio.Queue, audio_out: queue.Queue):
        """
        Modulate bytes into audio out
        """
        loop = asyncio.get_event_loop()

        with self.get_modulation_context() as modulate_byte:
            while True:
                packet = await data_in.get()
                for c in packet:
                    for frame in modulate_byte(c):
                        loop.call_soon_threadsafe(audio_out.put_nowait, frame)

    async def demodulate(self, audio_in: asyncio.Queue, data_out: asyncio.Queue):
        """
        Demodulate bytes from audio in
        """

        with self.get_demodulation_context() as demodulate_bit:
            while True:
                current_byte = 0
                for _ in range(8):
                    current_byte <<= 1
                    window = await audio_in.get()
                    current_byte += demodulate_bit(window)
                got_byte = current_byte.to_bytes(1, byteorder='little')
                data_out.put_nowait(got_byte)
                # print(f'{current_byte:#010b}'[2:], f' - {got_byte}')


class NonReturnToZeroModulator(Modulator):
    @contextlib.contextmanager
    def get_encoder(self):
        encode_last = 1
        encode_bits = {
            -1: '0',
            1: '1'
        }

        def encode(bit: str) -> str:
            nonlocal encode_last
            if bit == '0':
                return encode_bits[encode_last]
            encode_last *= -1
            return encode_bits[encode_last]

        yield encode

    @contextlib.contextmanager
    def get_decoder(self):
        decode_last = 1
        decode_bits = {
            -1: False,
            1: True
        }

        def decode(bit: bool) -> int:
            nonlocal decode_last
            if bit == decode_bits[decode_last]:
                return 0
            decode_last *= -1
            return 1

        yield decode


MODULATORS: typing.Dict[str, typing.Type[Modulator]] = {
    'standard': Modulator,
    'nrzi': NonReturnToZeroModulator
}
