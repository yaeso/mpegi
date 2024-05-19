import mimetypes

from pathlib import Path
from typing import BinaryIO

from utils import check_signature

# MPEGi standard -- Checks if MP3 follows ISO/IEC 11172-3:1993 guidelines.

MP3 = ".mp3"


class Standard:
    """
    Verifies if MP3 metadata complies with ISO/IEC 11172-3:1993 guidelines.

    Version         :   Tag identifiers (ID3v1, ID3v2)
    Metadata        :   Metadata validation
    Frame Sync      :   Frame sync patterns
    Bitrate Index   :   Bitrate indices
    Sampling Rate   :   Sampling rates (32kHz, 44.1kHz, 48kHz)

    etc. Complete after metadata and core are complete.
    """

    def __init__(self, audio: Path):
        self.audio = audio
        self.stream: BinaryIO = None

    def __enter__(self):
        self.stream = self.audio.open("rb")
        return self

    def verify(self):
        """
        Verifies if the given file is an MP3.

        Checks the file signature and extension.
        """
        signature = check_signature(self.audio)
        mime, _ = mimetypes.guess_type(self.audio)
        if mime:
            extension = mimetypes.guess_extension(mime)
            return extension == MP3 and signature == True

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stream:
            self.stream.close()


if __name__ == "__main__":
    audio = Path("imagematerial.mp3")
    with Standard(audio) as standard:
        print(standard.verify())
