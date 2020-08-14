import unittest
from aiofsk.ecc import HAMMING_8_4_CODE


class TestHammingECC(unittest.TestCase):
    def _test_error_correction(self, value: int, expected: int):
        decoded = HAMMING_8_4_CODE.decode(value)
        self.assertEqual(decoded, expected, f"{decoded:#06b} vs {expected:#06b}")

    def test_error_correction(self):
        self._test_error_correction(0b01100110, 0b1101)

        # flip 1 bit
        self._test_error_correction(0b01100111, 0b1101)
        self._test_error_correction(0b01100100, 0b1101)
        self._test_error_correction(0b01100010, 0b1101)
        self._test_error_correction(0b01101110, 0b1101)
        self._test_error_correction(0b01110110, 0b1101)
        self._test_error_correction(0b01000110, 0b1101)
        self._test_error_correction(0b00100110, 0b1101)
        self._test_error_correction(0b11100110, 0b1101)

        # flip 2 bits
        self._test_error_correction(0b01101111, -1)
        self._test_error_correction(0b01100000, -1)
        self._test_error_correction(0b00000110, -1)
        self._test_error_correction(0b01111110, -1)
