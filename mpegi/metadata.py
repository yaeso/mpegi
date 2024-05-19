import mimetypes

from pathlib import Path
from typing import BinaryIO

from genres import GENRES


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
            f"File Size (MB): {info_dict['file_size_in_mb']} MB\n"
            f"RFC: {info_dict['rfc']}\n"
        )


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


class Tag:
    """
    Reads TAGv1 and TAGv2 file structures and returns data.
    """

    TAGV1 = b"TAG"
    TAGV2 = b"ID3"

    def __init__(self, audio: Path):
        self.audio = audio
        self.stream: BinaryIO = None

    def __enter__(self):
        self.stream = self.audio.open("rb")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.stream:
            self.stream.close()

    def _v1(self):
        # tagv1 is always last 128 bytes in file
        self.stream.seek(-128, 2)
        tag = self.stream.read(3)
        if tag == self.TAGV1:

            self.stream.seek(-128, 2)
            return self.stream.read(128)

    def _content_v1(self):
        try:
            header = self._v1()
            if header is None:
                raise Exception("MP3 does not contain a TAGv1 space.")
        except Exception as e:
            print(e)

        metadata = {}
        metadata["Identifier"] = header[:3]
        metadata["Title"] = header[3:33]
        metadata["Artist"] = header[33:63]
        metadata["Album"] = header[63:93]
        metadata["Year"] = header[93:97]
        metadata["Comments"] = header[97:126]
        # metadata["Track"] = header[126:127]
        metadata["Genre"] = header[127:128]

        return self._clean_v1(metadata)

    def _clean_v1(self, metadata: dict):
        for label, value in metadata.items():
            value = value.decode("utf-8")

            if label == "Genre":
                idx = ord(value)
                value = GENRES[idx]
            else:
                value = value.replace("\x00", "").strip()

            if value == "":
                value = None

            metadata[label] = value

        return metadata

    def _v2(self):
        tag = self.stream.read(3)
        if tag == self.TAGV2:
            self.stream.seek(-3, 1)
            return self.stream.read(10)

    def _content_v2(self):
        try:
            stream = self._v2()
            if stream is None:
                raise Exception("MP3 does not contain a TAGv2 space.")
        except Exception as e:
            print(e)

        metadata = {}

        metadata["Identifier"] = stream[:3]
        metadata["Version"] = str(stream[3:4][0]) + "." + str(stream[4:5][0])

        metadata["Full Version"] = "ID3v2" + "." + metadata["Version"]

        # Ignore the following tags: https://id3.org/id3v2.4.0-structure
        # Only up to 2.4.0 is backwards compatible -- above versions are experimental
        if stream[3:4][0] >= 5:
            return self._clean_v2(metadata)

        flags = stream[5]  # 0b00000000
        metadata["Flags"] = flags
        metadata["Flags Hex"] = f"{flags:02x}"
        metadata["Flags Bits"] = f"{flags:08b}"

        # Below are the flag settings:

        # A set bit indicates unsynchronisation is applied on all frames.
        unsynchronisation = (flags & 0b10000000) >> 7
        # A set bit indicates the presence of an extended header.
        extended_header = (flags & 0b01000000) >> 6
        # SHALL always be set when the tag is in an experimental stage.
        experimental_indicator = (flags & 0b00100000) >> 5
        # A set bit indicates the presence of a footer at the end of the tag.
        footer_present = (flags & 0b00010000) >> 4

        metadata["Unsynchronisation"] = bool(unsynchronisation)
        metadata["Extended Header"] = bool(extended_header)
        metadata["Experimental Indicator"] = bool(experimental_indicator)
        metadata["Footer Present"] = bool(footer_present)

        # idx = 6
        if extended_header == 1:
            # Maybe add extended_header info support in the future:
            return self._clean_v2(metadata)

        # Check if other flags are cleared
        sequences = (0b00001000, 0b00000100, 0b00000010, 0b00000001)
        shift = 3
        for sequence in sequences:
            if (flags & sequence) >> shift == 1:
                metadata["Other Flags"] = "NOT CLEARED"
                print("Undefined flag(s) are set.")
                return self._clean_v2(metadata)

            shift -= 1

        metadata["Other Flags"] = "CLEARED"

        frames = {}
        idx = 10

        while idx < len(stream):
            frame_header = stream[idx : idx + 10]
            print(frame_header)
            frame_id = frame_header[:4].decode("ascii")
            frame_size = int.from_bytes(frame_header[4:8], byteorder="big")
            # frame_flags = frame_header[8:10]

            frame_body = stream[idx + 10 : idx + 10 + frame_size]
            encoding_byte = frame_body[0]
            frame_body = frame_body[1:]

            if encoding_byte == 0:
                encoding = "ISO-8859-1"
            elif encoding_byte == 1:
                encoding = "utf-16"
            elif encoding_byte == 2:
                encoding = "utf-16-be"
            else:
                encoding = "utf-8"

            frames[frame_id] = frame_body.decode(encoding, "ignore")
            idx += 10 + frame_size

        print(frames)

        return metadata


if __name__ == "__main__":
    audio = Path("kotov.mp3")
    info = Info(audio)
    print(info)
    with Tag(Path(audio)) as tag:
        print(tag._content_v2())
    # print(info.to_dict())
