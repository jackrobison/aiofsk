import typing


def hamming_distance(a: int, b: int) -> int:
    mask = a ^ b
    distance = 0
    while mask:
        distance += mask % 2
        mask >>= 1
    return distance


def hamming_code(data: int, size: int = 4):
    data_bits = tuple((data >> i) % 2 for i in range(size))
    parity = (
        data_bits[0] ^ data_bits[1] ^ data_bits[3],
        data_bits[0] ^ data_bits[2] ^ data_bits[3],
        data_bits[1] ^ data_bits[2] ^ data_bits[3]
    )
    parity = parity + (
        parity[0] ^ parity[1] ^ data_bits[0] ^ parity[2] ^ data_bits[1] ^ data_bits[2] ^ data_bits[3],
    )
    return (parity[3] * (1 << 0)) + \
           (data_bits[3] * (1 << 1)) + \
           (data_bits[2] * (1 << 2)) + \
           (data_bits[1] * (1 << 3)) + \
           (parity[2] * (1 << 4)) + \
           (data_bits[0] * (1 << 5)) + \
           (parity[1] * (1 << 6)) + \
           (parity[0] * (1 << 7))


class HammingSet(typing.NamedTuple):
    table: typing.Tuple[int, ...]

    @staticmethod
    def make_hamming_set(bits: int):
        return HammingSet(
            tuple(hamming_code(i, bits) for i in range((2 ** bits)))
        )

    def decode(self, encoded: int) -> int:
        """
        :param encoded: byte to decode
        :return: error corrected nibble (int), if the data is not correctable returns -1
        """
        off_by_one = None
        for key, code in enumerate(self.table):
            score = hamming_distance(encoded, code)
            if score == 0:
                return key
            if score == 1:
                if off_by_one:
                    return -1
                off_by_one = key
        if off_by_one is not None:
            return off_by_one
        return -1

    def encode(self, nibble: int) -> int:
        return self.table[nibble]


HAMMING_8_4_CODE = HammingSet.make_hamming_set(4)
