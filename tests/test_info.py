from pathlib import Path

from mpegi import Info


class TestInfo:

    def setup_class(self):
        audio = Path("imagematerial.mp3")
        self.info = Info(audio)
        print(self.info)

    def test_filename(self):
        assert self.info._fname() == "imagematerial.mp3"

    def test_mime(self):
        assert self.info._mime() == "audio/mpeg"

    def test_extension(self):
        assert self.info._fext() == ".mp3"

    def test_filesize(self):
        assert self.info._fsize() == 10421448

    def test_filesize_mb(self):
        assert self.info._fsize_to_mb() == 9.94

    def test_rfc(self):
        assert self.info._rfc() == 3003

    def test_to_dict(self):
        assert self.info.to_dict() == {
            "file_name": "imagematerial.mp3",
            "mime_type": "audio/mpeg",
            "file_extension": ".mp3",
            "file_size": 10421448,
            "file_size_in_mb": 9.94,
            "rfc": 3003,
        }
