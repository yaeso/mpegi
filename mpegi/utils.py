# MPEGi utils -- utility functions
from pathlib import Path


def check_signature(audio: Path) -> bool:
    """
    Validates an MP3 file by checking its file signature.

    Args:
        audio: Path to the MP3 audio file.

    Returns:
        True if the file signature matches known MP3 signatures, False otherwise.
    """
    VALID_ISO = [
        b"\x49\x44\x33",  # ID3
        b"\xFF\xFB",  # ÿû
        b"\xFF\xF3",  # ÿó
        b"\xFF\xF2",  # ÿò
    ]

    with audio.open("rb") as stream:
        signature = stream.read(3)

    return any(signature in s for s in VALID_ISO)


def rm_unsync(body: bytes) -> bytes:
    """
    Removes unsynchronization bytes from the given byte sequence.

    Unsynchronization is a process in ID3v2 tags to prevent false
    synchronization by adding a zero byte after every 0xFF byte. This
    function reverses that process by removing those zero bytes.

    See: https://id3.org/id3v2.4.0-structure -- 6.1

    Args:
        body (bytes): The byte sequence from which to remove unsynchronization bytes.

    Returns:
        bytes: The byte sequence with unsynchronization bytes removed.
    """
    return body.replace(b"\xFF\x00", b"\xFF")
