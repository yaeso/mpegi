import mimetypes

from pathlib import Path
from typing import BinaryIO

from genres import GENRES
from ptypes import PICTURE_TYPE


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
            return e

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
            return e

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

        tag_size_bytes = stream[6:10]
        size = (
            (stream[6] & 0x7F) << 21
            | (stream[7] & 0x7F) << 14
            | (stream[8] & 0x7F) << 7
            | (stream[9] & 0x7F)
        )
        tag_body = self.stream.read(size)

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

            frame_instance = Frames(frame_body, frame_id, frame_size, save_image=False)

            print(frame_id)
            processed_frame = frame_instance.process_frame()
            if processed_frame is not None:
                frames[frame_id] = processed_frame
                print(frames[frame_id])
                # metadata[frame_id] = frames[frame_id]
            idx += 10 + frame_size

        # return metadata


class Frames:
    """
    Class to handle frames and their decoding.

    Each frame is used for storing one piece of information, such as Artist or Album.
    A frame consists of a header and body.

    Header (10 Bytes):

    Bytes    Content
    0-3      Frame identifier
    4-7      Size
    8-9      Flags

    If the frame has a valid id, a Tuple will be returned in the following format:

        (ID, Information, Description, Frame Type, Frame Size)

    For example, if ID == TIT2:

        ("TIT2", "Kotov Syndrome", "TIT2", "TEXT_INFORMATION_FRAME", 200091)
    """

    MAP = {
        "COMM": ("COMMENTS", "_comm"),
        "TIT1": ("TEXT_INFORMATION_FRAMES", "_tit1"),
        "TIT2": ("TEXT_INFORMATION_FRAMES", "_tit2"),
        "TIT3": ("TEXT_INFORMATION_FRAMES", "_tit3"),
        "TALB": ("TEXT_INFORMATION_FRAMES", "_talb"),
        "TOAL": ("TEXT_INFORMATION_FRAMES", "_toal"),
        "TRCK": ("TEXT_INFORMATION_FRAMES", "_trck"),
        "TPOS": ("TEXT_INFORMATION_FRAMES", "_tpos"),
        "TSST": ("TEXT_INFORMATION_FRAMES", "_tsst"),
        "TSRC": ("TEXT_INFORMATION_FRAMES", "_tsrc"),
        "TPE1": ("INVOLVED_PERSONS_FRAMES", "_tpe1"),
        "TPE2": ("INVOLVED_PERSONS_FRAMES", "_tpe2"),
        "TPE3": ("INVOLVED_PERSONS_FRAMES", "_tpe3"),
        "TPE4": ("INVOLVED_PERSONS_FRAMES", "_tpe4"),
        "TOPE": ("INVOLVED_PERSONS_FRAMES", "_tope"),
        "TEXT": ("INVOLVED_PERSONS_FRAMES", "_text"),
        "TOLY": ("INVOLVED_PERSONS_FRAMES", "_toly"),
        "TCOM": ("INVOLVED_PERSONS_FRAMES", "_tcom"),
        "TMCL": ("INVOLVED_PERSONS_FRAMES", "_tmcl"),
        "TIPL": ("INVOLVED_PERSONS_FRAMES", "_tipl"),
        "TENC": ("INVOLVED_PERSONS_FRAMES", "_tenc"),
        "TBPM": ("DERIVED_SUBJECTIVE_PROPERTIES_FRAMES", "_tbpm"),
        "TLEN": ("DERIVED_SUBJECTIVE_PROPERTIES_FRAMES", "_tlen"),
        "TKEY": ("DERIVED_SUBJECTIVE_PROPERTIES_FRAMES", "_tkey"),
        "TLAN": ("DERIVED_SUBJECTIVE_PROPERTIES_FRAMES", "_tlan"),
        "TCON": ("DERIVED_SUBJECTIVE_PROPERTIES_FRAMES", "_tcon"),
        "TFLT": ("DERIVED_SUBJECTIVE_PROPERTIES_FRAMES", "_tflt"),
        "TMED": ("DERIVED_SUBJECTIVE_PROPERTIES_FRAMES", "_tmed"),
        "TMOO": ("DERIVED_SUBJECTIVE_PROPERTIES_FRAMES", "_tmoo"),
        "TCOP": ("RIGHTS_LICENSE_FRAMES", "_tcop"),
        "TPRO": ("RIGHTS_LICENSE_FRAMES", "_tpro"),
        "TPUB": ("RIGHTS_LICENSE_FRAMES", "_tpub"),
        "TOWN": ("RIGHTS_LICENSE_FRAMES", "_town"),
        "TRSN": ("RIGHTS_LICENSE_FRAMES", "_trsn"),
        "TRSO": ("RIGHTS_LICENSE_FRAMES", "_trso"),
        "TOFN": ("OTHER_TEXT_FRAMES", "_tofn"),
        "TDLY": ("OTHER_TEXT_FRAMES", "_tdly"),
        "TDEN": ("OTHER_TEXT_FRAMES", "_tden"),
        "TDOR": ("OTHER_TEXT_FRAMES", "_tdor"),
        "TDRC": ("OTHER_TEXT_FRAMES", "_tdrc"),
        "TYER": ("OTHER_TEXT_FRAMES", "_tyer"),
        "TDRL": ("OTHER_TEXT_FRAMES", "_tdrl"),
        "TDTG": ("OTHER_TEXT_FRAMES", "_tdtg"),
        "TSSE": ("OTHER_TEXT_FRAMES", "_tsse"),
        "TSOA": ("OTHER_TEXT_FRAMES", "_tsoa"),
        "TSOP": ("OTHER_TEXT_FRAMES", "_tsop"),
        "TSOT": ("OTHER_TEXT_FRAMES", "_tsot"),
        "TXXX": ("USER_DEFINED_INFORMATION_FRAME", "_txxx"),
        "WCOM": ("URL_LINK_FRAMES", "_wcom"),
        "WCOP": ("URL_LINK_FRAMES", "_wcop"),
        "WOAF": ("URL_LINK_FRAMES", "_woaf"),
        "WOAR": ("URL_LINK_FRAMES", "_woar"),
        "WOAS": ("URL_LINK_FRAMES", "_woas"),
        "WORS": ("URL_LINK_FRAMES", "_wors"),
        "WPAY": ("URL_LINK_FRAMES", "_wpay"),
        "WPUB": ("URL_LINK_FRAMES", "_wpub"),
        "WXXX": ("USER_DEFINED_URL_FRAME", "_wxxx"),
        "MCDI": ("MUSIC_CD_IDENTIFIER", "_mcdi"),
        "ETCO": ("EVENT_TIMING_CODES", "_etco"),
        "MLLT": ("MPEG_LOCATION_LOOKUP_TABLE", "_mllt"),
        "SYTC": ("SYNCHRONISED_TEMPO_CODES", "_sytc"),
        "USLT": ("UNSYNCRHONISED_LYRICS_TEXT_TRANSCRIPTION", "_uslt"),
        "SYLT": ("SYNCHRONIZED_LYRICS_TEXT_TRANSCRIPTION", "_sylt"),
        "RVA2": ("RELATIVE_VOLUME_ADJUSTMENT", "_rva2"),
        "EQU2": ("EQUALISATION", "_equ2"),
        "RVRB": ("REVERB", "_rvrb"),
        "APIC": ("ATTACHED_PICTURE", "_apic"),
        "GEOB": ("GENERAL_ENCAPSULATED_OBJECT", "_geob"),
        "PCNT": ("PLAY_COUNTER", "_pcnt"),
        "POPM": ("POPULARIMETER", "_popm"),
        "RBUF": ("RECOMMENDED_BUFFER_SIZE", "_rbuf"),
        "AENC": ("AUDIO_ENCRYPTION", "_aenc"),
        "LINK": ("LINKED_INFORMATION", "_link"),
        "POSS": ("POSITION_SYNCHRONIZATION_FRAME", "_poss"),
        "USER": ("TERMS_OF_USE_FRAME", "_user"),
        "OWNE": ("OWNERSHIP_FRAME", "_owne"),
        "COMR": ("COMMERCIAL_FRAME", "_comr"),
        "ENCR": ("ENCYRPTION_METHOD_REGISTRATION", "_encr"),
        "GRID": ("GROUP_IDENTIFICATION_REGISTRATION", "_grid"),
        "PRIV": ("PRIVATE_FRAME", "_priv"),
        "SIGN": ("SIGNATURE_FRAME", "_sign"),
        "SEEK": ("SEEK_FRAME", "_seek"),
        "ASPI": ("AUDIO_SEEK_POINT_INDEX", "_aspi"),
    }

    def __init__(self, body, id, size, save_image: bool = False):
        self.encoding = body[0]
        self.body = body[1:]
        self.id = id
        self.size = size
        self.save_image = save_image

    def process_frame(self):
        if self.id in self.MAP:
            c, m = self.MAP[self.id]
            if hasattr(self, m):
                frmethod = getattr(self, m)
                return frmethod()
        return None

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
        encoding = self._encode()
        try:
            language = self.body[:3].decode(encoding)
        except:
            try:
                language = self.body[:3].decode("utf-8")
            except:
                language = None

        description, null_sep, text = self.body[3:].partition(b"\x00")

        try:
            description = description.decode(encoding)
        except:
            description = None

        ftext = text.strip().decode(encoding, "ignore")
        ftext = "".join([char if 32 <= ord(char) <= 126 else " " for char in ftext])
        return {
            "ID": "COMM",
            "Language": language,
            "Description": description,
            "Text": ftext,
            "Contains": "Comments",
            "Part of": self.MAP["COMM"][0],
            "Frame Size": self.size,
        }

    def _tit1(self):
        encoding = self._encode()
        return {
            "ID": "TIT1",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Content Group Description",
            "Part of": self.MAP["TIT1"][0],
            "Frame Size": self.size,
        }

    def _tit2(self):
        encoding = self._encode()
        return {
            "ID": "TIT2",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Title/Songname/Content",
            "Part of": self.MAP["TIT2"][0],
            "Frame Size": self.size,
        }

    def _tit3(self):
        encoding = self._encode()
        return {
            "ID": "TIT3",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Subtitle/Description",
            "Part of": self.MAP["TIT3"][0],
            "Frame Size": self.size,
        }

    def _talb(self):
        encoding = self._encode()
        return {
            "ID": "TALB",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Album/Movie/Show",
            "Part of": self.MAP["TALB"][0],
            "Frame Size": self.size,
        }

    def _toal(self):
        encoding = self._encode()
        return {
            "ID": "TOAL",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Original Album/Movie/Show",
            "Part of": self.MAP["TOAL"][0],
            "Frame Size": self.size,
        }

    def _trck(self):
        encoding = self._encode()
        return {
            "ID": "TRCK",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Track Number/Position",
            "Part of": self.MAP["TRCK"][0],
            "Frame Size": self.size,
        }

    def _TPOS(self):
        encoding = self._encode()
        return {
            "ID": "TPOS",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Part of a Set",
            "Part of": self.MAP["TPOS"][0],
            "Frame Size": self.size,
        }

    def _tsst(self):
        encoding = self._encode()
        return {
            "ID": "TSST",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Set Subtitle",
            "Part of": self.MAP["TSST"][0],
            "Frame Size": self.size,
        }

    def _tsrc(self):
        encoding = self._encode()
        return {
            "ID": "TSRC",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "International Standard Recording Code [ISRC]",
            "Part of": self.MAP["TSRC"][0],
            "Frame Size": self.size,
        }

    def _tpe1(self):
        encoding = self._encode()
        return {
            "ID": "TPE1",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Artist/Performer/Soloist/Group",
            "Part of": self.MAP["TPE1"][0],
            "Frame Size": self.size,
        }

    def _tpe2(self):
        encoding = self._encode()
        return {
            "ID": "TPE2",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Band/Orchestra/Accompaniment",
            "Part of": self.MAP["TPE2"][0],
            "Frame Size": self.size,
        }

    def _tpe3(self):
        encoding = self._encode()
        return {
            "ID": "TPE3",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Conductor",
            "Part of": self.MAP["TPE3"][0],
            "Frame Size": self.size,
        }

    def _tpe4(self):
        encoding = self._encode()
        return {
            "ID": "TPE4",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Interpreted/Remixed/Modified by",
            "Part of": self.MAP["TPE4"][0],
            "Frame Size": self.size,
        }

    def _tope(self):
        encoding = self._encode()
        return {
            "ID": "TOPE",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Original Artist/Performer",
            "Part of": self.MAP["TOPE"][0],
            "Frame Size": self.size,
        }

    def _text(self):
        encoding = self._encode()
        return {
            "ID": "TEXT",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Lyricist",
            "Part of": self.MAP["TEXT"][0],
            "Frame Size": self.size,
        }

    def _toly(self):
        encoding = self._encode()
        return {
            "ID": "TOLY",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Original Lyricist",
            "Part of": self.MAP["TOLY"][0],
            "Frame Size": self.size,
        }

    def _tcom(self):
        encoding = self._encode()
        return {
            "ID": "TCOM",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Composer",
            "Part of": self.MAP["TCOM"][0],
            "Frame Size": self.size,
        }

    # tmcl and tipl output as Role1:Person1;Role2:Person2;..
    # so basic decoding *should* work
    # verify once a test mp3 is found, then return it as a dict
    def _tmcl(self):
        encoding = self._encode()
        return {
            "ID": "TMCL",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Musician Credits",
            "Part of": self.MAP["TMCL"][0],
            "Frame Size": self.size,
        }

    def _tipl(self):
        encoding = self._encode()
        return {
            "ID": "TIPL",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Involved People List",
            "Part of": self.MAP["TIPL"][0],
            "Frame Size": self.size,
        }

    def _tenc(self):
        encoding = self._encode()
        return {
            "ID": "TENC",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Encoded by",
            "Part of": self.MAP["TENC"][0],
            "Frame Size": self.size,
        }

    def _tbpm(self):
        encoding = self._encode()
        return {
            "ID": "TBPM",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "BPM",
            "Part of": self.MAP["TBPM"][0],
            "Frame Size": self.size,
        }

    def _tlen(self):
        encoding = self._encode()
        return {
            "ID": "TLEN",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Length of Audio File in Milliseconds",
            "Part of": self.MAP["TLEN"][0],
            "Frame Size": self.size,
        }

    def _tkey(self):
        encoding = self._encode()
        return {
            "ID": "TKEY",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Initial Key",
            "Part of": self.MAP["TKEY"][0],
            "Frame Size": self.size,
        }

    def _tlan(self):
        encoding = self._encode()
        return {
            "ID": "TLAN",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Language",
            "Part of": self.MAP["TLAN"][0],
            "Frame Size": self.size,
        }

    def _tcon(self):
        encoding = self._encode()
        return {
            "ID": "TCON",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Content Type (Genre)",
            "Part of": self.MAP["TCON"][0],
            "Frame Size": self.size,
        }

    def _tflt(self):
        encoding = self._encode()

        file_type = self.body.decode(encoding, "ignore").strip()

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

        description = types.get(file_type, "Unknown audio type")

        return {
            "ID": "TFLT",
            "File Type": file_type,
            "Description": description,
            "Contains": "File Type",
            "Part of": self.MAP["TFLT"][0],
            "Frame Size": self.size,
        }

    def _tmed(self):
        encoding = self._encode()
        media_type = self.body.decode(encoding, "ignore").strip()

        # Not gonna manually parse them
        # https://mutagen-specs.readthedocs.io/en/latest/id3/id3v2.4.0-frames.html#tmed
        return {
            "ID": "TMED",
            "Information": media_type,
            "Contains": "Media Type",
            "Part of": self.MAP["TMED"][0],
            "Frame Size": self.size,
        }

    def _tmoo(self):
        encoding = self._encode()
        return {
            "ID": "TMOO",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Mood",
            "Part of": self.MAP["TMOO"][0],
            "Frame Size": self.size,
        }

    def _tcop(self):
        encoding = self._encode()
        return {
            "ID": "TCOP",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Copyright Message",
            "Part of": self.MAP["TCOP"][0],
            "Frame Size": self.size,
        }

    def _tpro(self):
        encoding = self._encode()
        return {
            "ID": "TPRO",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Produced Notice",
            "Part of": self.MAP["TPRO"][0],
            "Frame Size": self.size,
        }

    def _tpub(self):
        encoding = self._encode()
        return {
            "ID": "TPUB",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Publisher",
            "Part of": self.MAP["TPUB"][0],
            "Frame Size": self.size,
        }

    def _town(self):
        encoding = self._encode()
        return {
            "ID": "TOWN",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "File owner/Licensee",
            "Part of": self.MAP["TOWN"][0],
            "Frame Size": self.size,
        }

    def _trsn(self):
        encoding = self._encode()
        return {
            "ID": "TRSN",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Internet Radio Station Name",
            "Part of": self.MAP["TRSN"][0],
            "Frame Size": self.size,
        }

    def _trso(self):
        encoding = self._encode()
        return {
            "ID": "TRSO",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Internet Radio Station Owner",
            "Part of": self.MAP["TRSO"][0],
            "Frame Size": self.size,
        }

    def _tfon(self):
        encoding = self._encode()
        return {
            "ID": "TFON",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Original Filename",
            "Part of": self.MAP["TFON"][0],
            "Frame Size": self.size,
        }

    def _tdly(self):
        encoding = self._encode()
        return {
            "ID": "TDLY",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Playlist Delay in Milliseconds",
            "Part of": self.MAP["TDLY"][0],
            "Frame Size": self.size,
        }

    def _tden(self):
        encoding = self._encode()
        return {
            "ID": "TDEN",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Encoding Time",
            "Part of": self.MAP["TDEN"][0],
            "Frame Size": self.size,
        }

    def _tdor(self):
        encoding = self._encode()
        return {
            "ID": "TDOR",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Original Release Time",
            "Part of": self.MAP["TDOR"][0],
            "Frame Size": self.size,
        }

    def _tdrc(self):
        encoding = self._encode()
        return {
            "ID": "TDRC",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Recording Time",
            "Part of": self.MAP["TDRC"][0],
            "Frame Size": self.size,
        }

    def _tyer(self):
        # same as tdrc but for 2.3
        encoding = self._encode()
        return {
            "ID": "TYER",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Recording Time",
            "Part of": self.MAP["TYER"][0],
            "Frame Size": self.size,
        }

    def _tdrl(self):
        encoding = self._encode()
        return {
            "ID": "TDRL",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Release Time",
            "Part of": self.MAP["TDRL"][0],
            "Frame Size": self.size,
        }

    def _tdtg(self):
        encoding = self._encode()
        return {
            "ID": "TDTG",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Tagging Time",
            "Part of": self.MAP["TDTG"][0],
            "Frame Size": self.size,
        }

    def _tsse(self):
        encoding = self._encode()
        return {
            "ID": "TSSE",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Software/Hardware & Settings Used for Encoding",
            "Part of": self.MAP["TSSE"][0],
            "Frame Size": self.size,
        }

    def _tsoa(self):
        encoding = self._encode()
        return {
            "ID": "TSOA",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Album Sort Order",
            "Part of": self.MAP["TSOA"][0],
            "Frame Size": self.size,
        }

    def _tsop(self):
        encoding = self._encode()
        return {
            "ID": "TSOP",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Performer Sort Order",
            "Part of": self.MAP["TSOP"][0],
            "Frame Size": self.size,
        }

    def _tsot(self):
        encoding = self._encode()
        return {
            "ID": "TSOT",
            "Information": self.body.decode(encoding, "ignore"),
            "Contains": "Title Sort Order",
            "Part of": self.MAP["TSOT"][0],
            "Frame Size": self.size,
        }

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

        return {
            "ID": "APIC",
            "MIME Type": mime_type,
            "Picture Type": PICTURE_TYPE[picture_type],
            "Description": description,
            "Picture Data Length": len(picture_data),
            "Image Saved": self.save_image,
            "Contains": "Attached Picture",
            "Part of": self.MAP["APIC"][0],
            "Frame Size": self.size,
        }


if __name__ == "__main__":
    audio1 = Path("kotov.mp3")
    audio2 = Path("imagematerial.mp3")
    # info = Info(audio)
    # print(info)
    with Tag(Path(audio1)) as tag:
        print("\n", tag._content_v2())

    with Tag(Path(audio2)) as tag:
        print("\n", tag._content_v2())

    # print(info.to_dict())
