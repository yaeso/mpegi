from pathlib import Path

from mpegi.namespace import (
    MPEG_AUDIO,
    LAYERS,
    BITRATE_INDEX,
    CHANNELS,
    JOINT_STEREO_MODE_EXTENSIONS_L1_2,
    JOINT_STEREO_MODE_EXTENSIONS_L3,
    SAMPLING_RATE_FREQUENCY,
    EMPHASIS,
)
from mpegi.utils import frame_header


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

        return bitrate

    def _verify_bitrate(self, bitrate):
        """
        For Layer II, there are some bitrate and mode combinations that are not allowed.

        When `get_bitrate()` is called on a Layer II audio file, this method will
        be run to verify that the combination with mode is valid.

        It will then return the original bitrate or '{bitrate} and {mode} combination is not allowed.'
        """
        ALL = [64, 96, 112, 128, 160, 192]
        SINGLE_CHANNEL = [32, 48, 56, 80]
        OTHER_CHANNELS = [224, 256, 320, 384]

        mode = self.get_channel()
        if bitrate in ALL:
            return bitrate

        if bitrate in SINGLE_CHANNEL and mode != "Mono (single channel)":
            return Exception(
                f"Combination of {bitrate} bitrate and {mode} mode is not allowed."
            )
        elif bitrate in OTHER_CHANNELS and mode == "Mono (single channel)":
            return Exception(
                f"Combination of {bitrate} bitrate and {mode} mode is not allowed."
            )

        return bitrate

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

    # ex
    def get_length(self):
        """Attempts to calculate frame length in bytes."""
        frame_length = None
        layer = self.get_layer()
        try:
            if layer == "Layer I":
                frame_length = (
                    (12 * self.get_bitrate()) / self.get_sample_rate()
                    + int(self.get_padding())
                ) * 4
            else:
                frame_length = int(
                    (144 * (self.get_bitrate() * 1000) / self.get_sample_rate())
                    + int(self.get_padding())
                )

        except Exception:
            return Exception("Issue with calculating frame length.")

        return frame_length

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
                Frame Length    {self.get_length()}
            """


if __name__ == "__main__":
    metadata = Metadata(Path("mp3/kotov.mp3"))
    print(metadata)
