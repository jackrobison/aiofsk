import numpy as np
import scipy.io.wavfile
from aiofsk.modulation import MODULATORS
from aiofsk.baud import DEFAULT_BAUD_OPTIONS


async def write_wav(wav_path: str, data: bytes, baud: int = 300, modulator: str = 'standard', amplitude=1.0):
    modulator = MODULATORS[modulator](
        DEFAULT_BAUD_OPTIONS.make_baud_nt(baud), amplitude
    )

    # frame_count = modulator.frame_size * 8  # prepend 8 bits of silence
    frame_count = (modulator.frame_size * 8 * len(data))
    wav_data = np.zeros((frame_count, 1))
    i = 0
    # for _ in range(modulator.frame_size * 8):
    #     wav_data[i] = [0.0]
    #     i += 1

    for character in data:
        for bit in modulator.iter_symbols(character):
            modulated = modulator.modulate_bit(bit)
            for sample in modulated:
                wav_data[i] = sample
                i += 1
    scipy.io.wavfile.write(wav_path, modulator.sample_rate, wav_data)


async def read_wav(wav_path: str, baud: int = 300, modulator: str = 'standard'):
    modulator = MODULATORS[modulator](
        DEFAULT_BAUD_OPTIONS.make_baud_nt(baud)
    )

    rate, data = scipy.io.wavfile.read(wav_path)

    frame_count = len(data) // modulator.frame_size
    offset = 0
    msg = b''
    with modulator.get_demodulation_context() as demodulate:
        current_byte = 0
        for frame_cnt in range(frame_count):
            frame = np.zeros((modulator.frame_size, 1))
            for i in range(modulator.frame_size):
                frame[i] = data[offset]
                offset += 1
            current_byte += demodulate(frame)
            if frame_cnt > 0 and ((frame_cnt + 1) % 8 == 0):
                msg += current_byte.to_bytes(1, byteorder='little')
                current_byte = 0
            else:
                current_byte <<= 1
    return msg
