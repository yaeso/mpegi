from pathlib import Path

from mpegi.metadata import Metadata


class TestMetadata:

    def setup_class(self):
        audio = Path("./mp3/imagematerial.mp3")
        self.metadata = Metadata(audio)

    def test_version(self):
        assert self.metadata.get_version() == "MPEG Version 1 (ISO/IEC 11172-3)"

    def test_layer(self):
        assert self.metadata.get_layer() == "Layer III"

    def test_crc(self):
        assert self.metadata.get_crc() == "1"

    def test_bitrate(self):
        assert self.metadata.get_bitrate() == 192

    def test_sample_rate(self):
        assert self.metadata.get_sample_rate() == 44100

    def test_padding(self):
        assert self.metadata.get_padding() == "0"

    def test_private(self):
        assert self.metadata.get_private() == "0"

    def test_channel(self):
        assert self.metadata.get_channel() == (
            "Joint Stereo",
            "Intensity Stereo [OFF] -- MS Stereo [ON]",
        )

    def test_copyright(self):
        assert self.metadata.get_copyright() == "0"

    def test_original(self):
        assert self.metadata.get_original() == "1"

    def test_emphasis(self):
        assert self.metadata.get_emphasis() == None

    def test_length(self):
        assert self.metadata.get_length() == 627
