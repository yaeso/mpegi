import pytest

from mpegi.metadata import Frames

DATA = [
    (
        b"\x01\xff\xfe0\x001\x00",
        "TRCK",
        7,
        {
            "ID": "TRCK",
            "Information": "01",
            "Contains": "Track Number/Position",
            "Part of": "TEXT_INFORMATION_FRAMES",
            "Frame Size": 7,
        },
    ),
    (
        b"\x01",
        "TENC",
        1,
        {
            "ID": "TENC",
            "Information": "",
            "Contains": "Encoded by",
            "Part of": "INVOLVED_PERSONS_FRAMES",
            "Frame Size": 1,
        },
    ),
    (
        b"\x00\x00",
        "WXXX",
        2,
        {
            "ID": "WXXX",
            "Description": "",
            "URL": "",
            "Contains": "Audio File URL Links",
            "Part of": "USER_DEFINED_URL_FRAME",
            "Frame Size": 2,
        },
    ),
    (
        b"\x01",
        "TCOP",
        1,
        {
            "ID": "TCOP",
            "Information": "",
            "Contains": "Copyright Message",
            "Part of": "RIGHTS_LICENSE_FRAMES",
            "Frame Size": 1,
        },
    ),
    (
        b"\x01",
        "TOPE",
        1,
        {
            "ID": "TOPE",
            "Information": "",
            "Contains": "Original Artist/Performer",
            "Part of": "INVOLVED_PERSONS_FRAMES",
            "Frame Size": 1,
        },
    ),
    (
        b"\x01",
        "TCOM",
        1,
        {
            "ID": "TCOM",
            "Information": "",
            "Contains": "Composer",
            "Part of": "INVOLVED_PERSONS_FRAMES",
            "Frame Size": 1,
        },
    ),
    (
        b"\x01\x00e\x00\xff\xfe\x00\x00\xff\xfeR\x00i\x00p\x00p\x00e\x00d\x00 \x00b\x00y\x00 \x00T\x00H\x00S\x00L\x00I\x00V\x00E\x00",
        "COMM",
        44,
        {
            "ID": "COMM",
            "Language": "e",
            "Description": "",
            "Text": "Ripped by THSLIV",
            "Contains": "Comments",
            "Part of": "COMMENTS",
            "Frame Size": 44,
        },
    ),
    (
        b"\x01\xff\xfe(\x003\x00)\x00D\x00a\x00n\x00c\x00e\x00",
        "TCON",
        19,
        {
            "ID": "TCON",
            "Information": "(3)Dance",
            "Contains": "Content Type (Genre)",
            "Part of": "DERIVED_SUBJECTIVE_PROPERTIES_FRAMES",
            "Frame Size": 19,
        },
    ),
    (
        b"\x01\xff\xfe2\x000\x000\x007\x00",
        "TYER",
        11,
        {
            "ID": "TYER",
            "Information": "2007",
            "Contains": "Recording Time",
            "Part of": "OTHER_TEXT_FRAMES",
            "Frame Size": 11,
        },
    ),
    (
        b"\x01\xff\xfeI\x00 \x00C\x00a\x00n\x00 \x00W\x00a\x00l\x00k\x00 \x00O\x00n\x00 \x00W\x00a\x00t\x00e\x00r\x00 \x00I\x00 \x00C\x00a\x00n\x00 \x00F\x00l\x00y\x00",
        "TALB",
        61,
        {
            "ID": "TALB",
            "Information": "I Can Walk On Water I Can Fly",
            "Contains": "Album/Movie/Show",
            "Part of": "TEXT_INFORMATION_FRAMES",
            "Frame Size": 61,
        },
    ),
    (
        b"\x01\xff\xfeB\x00a\x00s\x00s\x00h\x00u\x00n\x00t\x00e\x00r\x00",
        "TPE1",
        23,
        {
            "ID": "TPE1",
            "Information": "Basshunter",
            "Contains": "Artist/Performer/Soloist/Group",
            "Part of": "INVOLVED_PERSONS_FRAMES",
            "Frame Size": 23,
        },
    ),
    (
        b"\x01\xff\xfeI\x00 \x00C\x00a\x00n\x00 \x00W\x00a\x00l\x00k\x00 \x00O\x00n\x00 \x00W\x00a\x00t\x00e\x00r\x00 \x00I\x00 \x00C\x00a\x00n\x00 \x00F\x00l\x00y\x00",
        "TIT2",
        61,
        {
            "ID": "TIT2",
            "Information": "I Can Walk On Water I Can Fly",
            "Contains": "Title/Songname/Content",
            "Part of": "TEXT_INFORMATION_FRAMES",
            "Frame Size": 61,
        },
    ),
]


@pytest.mark.parametrize("body, id, size, expected", DATA)
def test_frame(body, id, size, expected):
    instance = Frames(body, id, size)
    frame = instance.process_frame()
    assert frame == expected
