from pathlib import Path
from typing import BinaryIO, Tuple, Union

from mpegi.namespace import GENRES, PICTURE_TYPE
from mpegi.utils import rm_unsync


class Tag:
    """
    Reads TAGv1 and TAGv2 file structures and returns stored data.

    Usage:
        audio = Path('audio.mp3')
        tag = Tag(audio)
        print(tag)
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

    def get(self):
        """
        Determines which TAG version the given audio file is
        and runs the corresponding method.
        """
        stream = self.get_stream()

        if stream is None:
            raise Exception("MP3 does not contain a TAGv1 or TAGv2 space.")

        if isinstance(stream, tuple) and isinstance(stream[0], str):
            get_tag = getattr(self, stream[0])
            return get_tag(stream[1])

        if isinstance(stream[0], bytes):
            return self.get_v1(stream[0]), self.get_v2(stream[1])

        raise Exception("Unexpected stream format.")

    def get_stream(self) -> Union[None, Tuple[bytes, bytes], Tuple[str, bytes]]:
        """
        Gets the byte stream for either TAG space.

        If both TAG spaces exist, return a Tuple containg both headers.

        If neither TAG space exists, return None.
        """
        # Account for both TAG spaces existing
        headerv1 = None
        headerv2 = None

        # Check for TAGv1 at the end of the file
        # TAGv1 is always the last 128 bytes in the file (if present)
        self.stream.seek(-128, 2)
        tag = self.stream.read(3)
        if tag == self.TAGV1:
            self.stream.seek(-128, 2)
            headerv1 = self.stream.read(128)

        # Check for TAGv2 at the beginning of the file
        self.stream.seek(0)
        tag = self.stream.read(3)
        if tag == self.TAGV2:
            self.stream.seek(-3, 1)
            headerv2 = self.stream.read(10)

        if headerv1 and headerv2:
            return (headerv1, headerv2)

        elif headerv1:
            return ("get_v1", headerv1)

        elif headerv2:
            return ("get_v2", headerv2)

        else:
            return None

    def get_v1(self, stream: bytes):
        """
        Get data from TAGv1 space.
        """
        metadata = {}

        metadata["Identifier"] = stream[:3]
        metadata["Title"] = stream[3:33]
        metadata["Artist"] = stream[33:63]
        metadata["Album"] = stream[63:93]
        metadata["Year"] = stream[93:97]
        metadata["Comments"] = stream[97:126]
        # Ignoring potential Track Number on 126
        # metadata["Track"] = stream[126:127]
        metadata["Genre"] = stream[127:128]

        return self._clean(metadata)

    def _clean(self, metadata: dict):
        """
        Cleans data from TAGV1 space.
        """
        for label, value in metadata.items():
            if isinstance(value, bytes):
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

    def get_v2(self, stream: bytes):
        """
        Gets data from TAGv2 space.
        """
        metadata = {}

        metadata["Identifier"] = stream[:3]
        metadata["Version"] = str(stream[3:4][0]) + "." + str(stream[4:5][0])
        metadata["Full Version"] = "ID3v2" + "." + metadata["Version"]

        # Ignore the following tags: https://id3.org/id3v2.4.0-structure
        # Only up to 2.4.0 is backwards compatible -- above versions are experimental
        if stream[3:4][0] >= 5:
            return metadata

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
            return "Extended Header"

        # Check if other flags are cleared
        sequences = (0b00001000, 0b00000100, 0b00000010, 0b00000001)
        shift = 3
        for sequence in sequences:
            if (flags & sequence) >> shift == 1:
                metadata["Other Flags"] = "NOT CLEARED"
                print("Undefined flag(s) are set.")
                return metadata

            shift -= 1

        metadata["Other Flags"] = "CLEARED"

        size = (
            (stream[6] & 0x7F) << 21
            | (stream[7] & 0x7F) << 14
            | (stream[8] & 0x7F) << 7
            | (stream[9] & 0x7F)
        )
        tag_body = self.stream.read(size)

        if unsynchronisation:
            tag_body = rm_unsync(tag_body)

        frames = {}
        idx = 0

        while idx < len(tag_body):
            frame_header = tag_body[idx : idx + 10]
            if len(frame_header) < 10:
                break

            frame_id = frame_header[:4].decode("ascii")

            frame_size = int.from_bytes(frame_header[4:8], byteorder="big")
            if frame_size == 0:
                idx += 10
                continue

            frame_body = tag_body[idx + 10 : idx + 10 + frame_size]

            if not frame_body:
                idx += 10 + frame_size
                continue

            frame_instance = Frames(
                frame_body,
                frame_id,
                frame_size,
                save_image=False,
            )

            processed_frame = frame_instance.process_frame()
            if processed_frame is not None:
                metadata[frame_id] = processed_frame[1]
            idx += 10 + frame_size

        return metadata


class Frames:
    """
    Class to handle frames and their decoding.

    Each frame is used for storing one piece of information, such as Artist or Album.
    """

    def __init__(self, body, id, size, save_image: bool = False):
        self.body = body[1:]
        self.encoding = body[0]
        self.full_body = body
        self.id = id
        self.size = size
        self.save_image = save_image

    def process_frame(self):
        # Tag that needs its own method
        attr = "_" + self.id.lower()
        if hasattr(self, attr):
            frm = getattr(self, attr)
            return frm()

        # Invalid Tag
        if self.size < 1:
            return None

        else:
            try:
                data = self.decode_frame(self.id)
            except Exception:
                raise Exception("Invalid Frame Identifier")
                return

        return data

    def decode_frame(self, id: str):
        """
        Decodes frames that have the following format:

        | Text encoding     $xx                                    |
        | Information       <text string(s) according to encoding> |

        OR a User Defined Frame:

        | Text encoding     $xx                                          |
        | Description       <text string according to encoding> $00 (00) |
        | Value             <text string according to encoding>          |

        OR a URL Link/Music CD Identifier:

        | URL/CD TOC              <text string> |

        Other frames have their own method.
        """
        # user defined has format of encoding, description, text
        if id == "TXXX" or id == "WXXX":
            encoding = self._encode()
            description, null_sep, text = self.body.partition(b"\x00")
            description = description.decode(encoding, "ignore").strip()
            text = text.decode(encoding, "ignore").strip()
            return (id, (description, text))

        # url text frame has format of just url, or MCDI
        # Attempt at getting URL Link Frames
        if (
            id == "MCDI"
            or id.startswith("W")
            and not id.startswith("WXXX")
            and len(id) == 4
        ):
            if id == "MCDI":
                encoding = self._encode()
                information = self.full_body.decode(encoding, "ignore").replace(
                    "\x00", ""
                )
            else:
                information = self.full_body.decode("ISO-8859-1", "ignore").replace(
                    "\x00", ""
                )

            return (id, information)

        else:
            encoding = self._encode()
            information = self.body.decode(encoding, "ignore").replace("\x00", "")

            if id == "TFLT":
                types = {
                    "MIME": "MIME type follows",
                    "MPG": "MPEG Audio",
                    "/1": "MPEG 1/2 layer I",
                    "/2": "MPEG 1/2 layer II",
                    "/3": "MPEG 1/2 layer III",
                    "/2.5": "MPEG 2.5",
                    "/AAC": "Advanced audio compression",
                    "VQF": "Transform-domain Weighted Interleave Vector Quantisation",
                    "PCM": "Pulse Code Modulated audio",
                }

                information = types.get(information, "Unknown audio type")

            return (id, information)

    def _encode(self):
        if self.encoding == 0:
            return "ISO-8859-1"
        elif self.encoding == 1:
            return "utf-16"
        elif self.encoding == 2:
            return "utf-16-be"
        else:
            return "utf-8"

    def _comm(self):
        # come back to this later
        # text and desc seem to work on some and not others
        encoding = self._encode()

        try:
            language = self.body[:3].decode("ISO-8859-1").replace("\x00", "")
        except Exception as e:
            language = None
            print(f"Error decoding {self.id} language: {e}\n")

        description, null_sep, text = self.body[3:].partition(b"\x00")

        try:
            description = description.decode(encoding)
        except Exception as e:
            description = None
            print(f"Error decoding {self.id} description: {e}\n")

        try:
            ftext = text.strip(b"\x00").decode(encoding, "ignore")
            ftext = "".join(
                [char if 32 <= ord(char) <= 126 else char for char in ftext]
            )
        except Exception as e:
            ftext = None
            print(f"Error decoding {self.id} text: {e}\n")

        return (self.id, (description, ftext))

    def _etoc(self):
        return "Not Implemented"

    def _mllt(self):
        return "Not Implemented"

    def _sytc(self):
        timestamp_format = self.body[0]
        tempo_codes = self.body[1]

        timestamp_desc = {
            1: "Absolute time, 32 bit sized, using MPEG frames as unit",
            2: "Absolute time, 32 bit sized, using milliseconds as unit",
        }.get(timestamp_format, "Unknown format")

        # RANGE = 2 - 510BPM
        # timestamp format $01 MPEG frames
        # timestamp format $02 milliseconds

        RESERVED = {
            0: "Beat-free time period",
            1: "Single beat-stroke followed by a beat-free period",
        }

        return "Not Implemented"

    def _uslt(self):
        encoding = self._encode()

        try:
            language = self.body[:3].decode("ISO-8859-1").replace("\x00", "")
        except Exception as e:
            language = None
            print(f"Error decoding language: {e}")

        description, null_sep, lyrics = self.body[3:].partition(b"\x00")

        try:
            description = description.decode(encoding)
        except Exception as e:
            description = None
            print(f"Error decoding description: {e}")

        try:
            lyrics = lyrics.strip(b"\x00").decode(encoding, "ignore")
            lyrics = "".join(
                [char if 32 <= ord(char) <= 126 else char for char in lyrics]
            )
        except Exception as e:
            lyrics = None
            print(f"Error decoding lyrics: {e}")

        return (self.id, (description, lyrics))

    def _sylt(self):
        encoding = self._encode()

        try:
            language = self.body[:3].decode("ISO-8859-1").replace("\x00", "")
        except Exception as e:
            language = None
            print(f"Error decoding language: {e}")

        timestamp_byte = self.body[3]
        timestamp_format = {
            1: "Absolute time, 32 bit sized, using MPEG frames as unit",
            2: "Absolute time, 32 bit sized, using milliseconds as unit",
        }.get(timestamp_byte, "Unknown format")

        content_type_byte = self.body[4]
        content_type = {
            0: "Other",
            1: "Lyrics",
            2: "Text transcription",
            3: "Movement/part name",
            4: "Events",
            5: "Chord",
            6: "Trivia",
            7: "URLs to webpages",
            8: "URLs to images",
        }.get(content_type_byte, "Unknown content type")

        try:
            description_end = self.body[5:].find(b"\x00")
            if description_end == -1:
                description = self.body[5:].decode(encoding, "ignore").strip()
            else:
                description = (
                    self.body[5 : 5 + description_end]
                    .decode(encoding, "ignore")
                    .strip()
                )
        except Exception as e:
            description = None
            print(f"Error decoding description: {e}")

        # all methods that return "Not Implemented"
        # will be implemented after manual tests are created
        return "Not Implemented"

    def _apic(self):
        encoding = self._encode()

        mime_type, null_sep, frame_body = self.body.partition(b"\x00")
        mime_type = mime_type.decode("utf-8")

        picture_type = frame_body[0]
        frame_body = frame_body[1:]

        description, null_sep, frame_body = frame_body.partition(b"\x00")
        description = description.decode(encoding)

        picture_data = frame_body

        if self.save_image:
            if picture_type != 2:
                with open(f"{description}.jpg", "wb") as file:
                    file.write(picture_data)
                    print(f"Image saved to {description}.jpg")

            else:
                with open(f"{description}.png", "wb") as file:
                    file.write(picture_data)
                    print(f"Image saved to {description}.png")

        return (self.id, (mime_type, PICTURE_TYPE[picture_type], description))


if __name__ == "__main__":
    audio = Path("kotov.mp3")

    with Tag(audio) as tag:
        metadata = tag.get()
        print(metadata)
