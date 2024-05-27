from pathlib import Path
from typing import BinaryIO

from mpegi.utils import frame_header

# 00 refers to each byte, i suppose?
# xx xx

MPEG_AUDIO = {
    "00": "MPEG Version 2.5",
    "01": "RESERVED",
    "10": "MPEG Version 2 (ISO/IEC 13818-3)",
    "11": "MPEG Version 1 (ISO/IEC 11172-3)",
}

LAYERS = {"00": "RESERVED", "01": "Layer III", "10": "Layer II", "11": "Layer I"}

# CRC = {"0": "Protected by CRC (16bit CRC follows header)", "1": "Not Protected"}

BITRATE_INDEX = {
    "0000": {
        "V1_L1": "FREE",
        "V1_L2": "FREE",
        "V1_L3": "FREE",
        "V2_L1": "FREE",
        "V2_L2_3": "FREE",
    },
    "0001": {"V1_L1": 32, "V1_L2": 32, "V1_L3": 32, "V2_L1": 32, "V2_L2_3": 8},
    "0010": {"V1_L1": 64, "V1_L2": 48, "V1_L3": 40, "V2_L1": 48, "V2_L2_3": 16},
    "0011": {"V1_L1": 96, "V1_L2": 56, "V1_L3": 48, "V2_L1": 56, "V2_L2_3": 24},
    "0100": {"V1_L1": 128, "V1_L2": 64, "V1_L3": 56, "V2_L1": 64, "V2_L2_3": 32},
    "0101": {"V1_L1": 160, "V1_L2": 80, "V1_L3": 64, "V2_L1": 80, "V2_L2_3": 40},
    "0110": {"V1_L1": 192, "V1_L2": 96, "V1_L3": 80, "V2_L1": 96, "V2_L2_3": 48},
    "0111": {"V1_L1": 224, "V1_L2": 112, "V1_L3": 96, "V2_L1": 112, "V2_L2_3": 56},
    "1000": {"V1_L1": 256, "V1_L2": 128, "V1_L3": 112, "V2_L1": 128, "V2_L2_3": 64},
    "1001": {"V1_L1": 288, "V1_L2": 160, "V1_L3": 128, "V2_L1": 144, "V2_L2_3": 80},
    "1010": {"V1_L1": 320, "V1_L2": 192, "V1_L3": 160, "V2_L1": 160, "V2_L2_3": 96},
    "1011": {"V1_L1": 352, "V1_L2": 224, "V1_L3": 192, "V2_L1": 176, "V2_L2_3": 112},
    "1100": {"V1_L1": 384, "V1_L2": 256, "V1_L3": 224, "V2_L1": 192, "V2_L2_3": 128},
    "1101": {"V1_L1": 416, "V1_L2": 320, "V1_L3": 256, "V2_L1": 224, "V2_L2_3": 144},
    "1110": {"V1_L1": 448, "V1_L2": 384, "V1_L3": 320, "V2_L1": 256, "V2_L2_3": 160},
    "1111": {
        "V1_L1": "BAD",
        "V1_L2": "BAD",
        "V1_L3": "BAD",
        "V2_L1": "BAD",
        "V2_L2_3": "BAD",
    },
}

CHANNELS = {
    "00": "Stereo",
    "01": "Joint Stereo",
    "10": "Dual",
    "11": "Mono (single channel)",
}

JOINT_STEREO_MODE_EXTENSIONS_L1_2 = {
    "00": "Bands 4 to 31",
    "01": "Bands 8 to 31",
    "10": "Bands 12 to 31",
    "11": "Bands 16 to 31",
}
JOINT_STEREO_MODE_EXTENSIONS_L3 = {
    "00": "Intensity Stereo [OFF] -- MS Stereo [Off]",
    "01": "Intensity Stereo [ON] -- MS Stereo [Off]",
    "10": "Intensity Stereo [OFF] -- MS Stereo [ON]",
    "11": "Intensity Stereo [ON] -- MS Stereo [ON]",
}

SAMPLING_RATE_FREQUENCY = {
    "00": 44100,  # Hz 44.1kHz
    "01": 48000,  # Hz 48kHz
    "10": 32000,  # Hz 32kHz
    "11": "RESERVED",
}

EMPHASIS = {
    "00": None,
    "01": "50/15 ms",
    "10": "RESERVED",
    "11": "CCIT J.17",
}


class Metadata:
    """
    Obtains metadata from MP3.
    """

    def __init__(self, audio: Path):
        self.sync = frame_header(audio)[0]
        self.header = str(frame_header(audio)[1])

    def get_header(self):
        """Returns frame header."""
        return self.header

    def get_sync(self):
        """Returns frame sync bits."""
        return self.sync

    def get_version(self):
        """Returns MPEG Version ID"""
        return MPEG_AUDIO[self.header[11:13]]

    def get_layer(self):
        """Layer"""
        return LAYERS[self.header[13:15]]

    def get_crc(self):
        """Returns CRC Protection bit."""
        return self.header[15]

    def get_bitrate(self):
        """Returns bitrate."""
        # dependent on version and layer
        version = self.get_version()
        layer = self.get_layer()

        if version == "RESERVED" or layer == "RESERVED":
            return "BAD"

        if (
            version == "MPEG Version 2.5"
            or version == "MPEG Version 2 (ISO/IEC 13818-3)"
        ):
            if layer == "Layer I":
                verlay = "V2_L1"
            else:
                verlay = "V2_L2_3"

        elif version == "MPEG Version 1 (ISO/IEC 11172-3)":
            if layer == "Layer I":
                verlay = "V1_L1"
            elif layer == "Layer II":
                verlay = "V1_L2"
            else:
                verlay = "V1_L3"

        bitrate = BITRATE_INDEX[self.header[16:20]][verlay]
        if layer == "Layer II" and bitrate != "FREE" and bitrate != "BAD":
            return self._verify_bitrate(bitrate)

        return BITRATE_INDEX[self.header[16:20]][verlay]

    def _verify_bitrate(self, bitrate):
        """
        For Layer II, there are some bitrate and mode combinations that are not allowed.

        When `get_bitrate()` is called on a Layer II audio file, this method will
        be run to verify that the combination with mode is valid.

        It will then return the original bitrate or '{bitrate} and {mode} combination is not allowed.'
        """
        return

    def get_sample_rate(self):
        """Returns audio sample rate in Hz."""
        return SAMPLING_RATE_FREQUENCY[self.header[20:22]]

    def get_padding(self):
        """Returns padding bit."""
        return self.header[22]

    def get_private(self):
        """Returns private bit."""
        return self.header[23]

    def get_channel(self):
        """Returns channel mode as well as extension if Joint Stereo."""
        channel = CHANNELS[self.header[24:26]]
        if channel == "Joint Stereo":
            return (channel, self._get_extension())

        return channel

    def _get_extension(self):
        """Returns the mode extension."""
        layer = self.get_layer()
        if layer == "Layer III":
            return JOINT_STEREO_MODE_EXTENSIONS_L3[self.header[26:28]]

        return JOINT_STEREO_MODE_EXTENSIONS_L1_2[self.header[26:28]]

    def get_copyright(self):
        """Returns copyright bit."""
        return self.header[28]

    def get_original(self):
        """Returns original media bit."""
        return self.header[29]

    def get_emphasis(self):
        """Returns emphasis."""
        return EMPHASIS[self.header[30:32]]

    def __str__(self):
        return f"""
                Version         {self.get_version()}
                Layer           {self.get_layer()}
                CRC             {self.get_crc()}
                Bitrate         {self.get_bitrate()}
                Sample Rate     {self.get_sample_rate()}
                Padding         {self.get_padding()}
                Private         {self.get_private()}
                Channel         {self.get_channel()}
                Copyright       {self.get_copyright()}
                Original        {self.get_original()}
                Emphasis        {self.get_emphasis()}
                Frame Length    {self.get_frame_length()}
            """

    # ex
    def get_frame_length(self):
        """Attempts to calculate frame length."""
        frame_length = None
        try:
            frame_length = int(
                (144 * (self.get_bitrate() * 1000) / self.get_sample_rate())
                + int(self.get_padding())
            )

        except Exception:
            return Exception("Issue with calculating frame length.")

        return frame_length
