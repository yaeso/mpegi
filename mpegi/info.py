import mimetypes

from pathlib import Path


class Info:
    """
    Extracts basic information from an MP3 file.

    This class provides methods to retrieve metadata and properties of an MP3 file
    such as its MIME type, file extension, name, size, size in megabytes, and the RFC.

    Usage:
        audio = Path(audio.mp3)
        info = Info(audio)
        print(info)
    """

    def __init__(self, audio: Path):
        self.audio = audio

    def _fname(self):
        return self.audio.name

    def _mime(self):
        mime, _ = mimetypes.guess_type(self.audio)
        return mime

    def _fext(self):
        if self._mime():
            return mimetypes.guess_extension(self._mime())

    def _fsize(self):
        return self.audio.stat().st_size

    def _fsize_to_mb(self):
        return round(self._fsize() / (2**20), 2)

    def _rfc(self):
        return 3003

    def to_dict(self):
        return {
            "file_name": self._fname(),
            "mime_type": self._mime(),
            "file_extension": self._fext(),
            "file_size": self._fsize(),
            "file_size_in_mb": self._fsize_to_mb(),
            "rfc": self._rfc(),
        }

    def __str__(self):
        info_dict = self.to_dict()
        return (
            f"File Name: {info_dict['file_name']}\n"
            f"MIME Type: {info_dict['mime_type']}\n"
            f"File Extension: {info_dict['file_extension']}\n"
            f"File Size: {info_dict['file_size']} bytes\n"
            f"File Size (mb): {info_dict['file_size_in_mb']} mb\n"
            f"RFC: {info_dict['rfc']}\n"
        )
