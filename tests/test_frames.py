import pytest

from mpegi.frames import Frames

DATA = [
    (
        b"\x01\xff\xfe0\x001\x00",
        "TRCK",
        7,
        ("TRCK", "01"),
    ),
    (
        b"\x01",
        "TENC",
        1,
        ("TENC", ""),
    ),
    (
        b"\x00\x00",
        "WXXX",
        2,
        ("WXXX", ("", "")),
    ),
    (
        b"\x01",
        "TCOP",
        1,
        ("TCOP", ""),
    ),
    (
        b"\x01",
        "TOPE",
        1,
        ("TOPE", ""),
    ),
    (
        b"\x01",
        "TCOM",
        1,
        ("TCOM", ""),
    ),
    (
        b"\x01\x00e\x00\xff\xfe\x00\x00\xff\xfeR\x00i\x00p\x00p\x00e\x00d\x00 \x00b\x00y\x00 \x00T\x00H\x00S\x00L\x00I\x00V\x00E\x00",
        "COMM",
        44,
        ("COMM", ("", "Ripped by THSLIV")),
    ),
    (
        b"\x01\xff\xfe(\x003\x00)\x00D\x00a\x00n\x00c\x00e\x00",
        "TCON",
        19,
        ("TCON", "(3)Dance"),
    ),
    (
        b"\x01\xff\xfe2\x000\x000\x007\x00",
        "TYER",
        11,
        ("TYER", "2007"),
    ),
    (
        b"\x01\xff\xfeI\x00 \x00C\x00a\x00n\x00 \x00W\x00a\x00l\x00k\x00 \x00O\x00n\x00 \x00W\x00a\x00t\x00e\x00r\x00 \x00I\x00 \x00C\x00a\x00n\x00 \x00F\x00l\x00y\x00",
        "TALB",
        61,
        ("TALB", "I Can Walk On Water I Can Fly"),
    ),
    (
        b"\x01\xff\xfeB\x00a\x00s\x00s\x00h\x00u\x00n\x00t\x00e\x00r\x00",
        "TPE1",
        23,
        ("TPE1", "Basshunter"),
    ),
    (
        b"\x01\xff\xfeI\x00 \x00C\x00a\x00n\x00 \x00W\x00a\x00l\x00k\x00 \x00O\x00n\x00 \x00W\x00a\x00t\x00e\x00r\x00 \x00I\x00 \x00C\x00a\x00n\x00 \x00F\x00l\x00y\x00",
        "TIT2",
        61,
        ("TIT2", "I Can Walk On Water I Can Fly"),
    ),
]


@pytest.mark.parametrize("body, id, size, expected", DATA)
def test_frame(body, id, size, expected):
    instance = Frames(body, id, size)
    frame = instance.process_frame()
    print(expected)
    assert frame == expected
