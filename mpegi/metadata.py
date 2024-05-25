import mimetypes

from pathlib import Path
from typing import BinaryIO

from mpegi.genres import GENRES
from mpegi.ptypes import PICTURE_TYPE
from mpegi.utils import rm_unsync

# 00 refers to each byte, i suppose?
# xx xx

MP3_CHANNELS = {
    # 00: "Stereo",
    # 10: "Joint Stereo",
    # 10: "Dual",
    # 11: "Mono (single channel)",
}

JOINT_STEREO_MODE_EXTENSIONS = {
    # 00: "Intensity Stereo [OFF] -- MS Stereo [Off]",
    # 01: "Intensity Stereo [ON] -- MS Stereo [Off]",
    # 10: "Intensity Stereo [OFF] -- MS Stereo [ON]",
    # 11: "Intensity Stereo [ON] -- MS Stereo [ON]",
}

SAMPLING_RATE_FREQUENCY = {
    # 00: 44100,  # Hz 44.1kHz
    # 01: 48000,  # Hz 48kHz
    # 10: 32000,  # Hz 32kHz
    # 11: "RESERVED",
}


class Metadata:
    """
    Obtains metadata from input MP3.
    """

    def __init__(self, audio: Path):
        self.audio = audio
        self.stream: BinaryIO = None

    def __enter__(self):
        self.stream = self.audio.open("rb")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stream:
            self.stream.close()

    def _header(self):
        return

    def _sync(self):
        return

    def _version(self):
        return

    def _mpeg_version(self):
        return

    def _layer(self):
        return

    def _crc(self):
        return

    def _bitrate(self):
        # will probably be annoying
        return

    def _sample_rate(self):
        return

    def _padding(self):
        return

    def _channel(self):
        return

    def _mode(self):
        return

    def _copyright(self):
        return

    def _original(self):
        return

    def _emphasis(self):
        return

    # ex
    def _frame_len(self):
        return int((144 * self._bitrate() / self._sample_rate()) + self._padding())
