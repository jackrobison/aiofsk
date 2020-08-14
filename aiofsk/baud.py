import typing


class BaudRate(typing.NamedTuple):
    baud: int
    sample_rate: int
    frame_size: int


class BaudRateOptions(typing.NamedTuple):
    bauds: typing.Tuple[int, ...]
    sample_rate: int
    default: int

    def make_baud_nt(self, baud: int):
        assert baud in self.bauds and self.sample_rate % baud == 0
        return BaudRate(baud, self.sample_rate, self.sample_rate // baud)


DEFAULT_BAUD_OPTIONS = BaudRateOptions(
    bauds=(30, 300, 600, 1200, 1800, 2400),
    sample_rate=48000,
    default=300
)

TONES = {
    '0': 1200,
    '1': 2400
}
