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


def frame_header(audio: Path) -> bytes:
    """
    Retrieves the frame header.

    Ensures valid frame sync and header size.

    Args:
        audio (Path): The MP3 file.

    Returns:
        Tuple: The frame sync bits and the frame header.
    """
    with audio.open("rb") as stream:

        # Account for TAGv2 space at start of file
        stream.seek(0)
        tag = stream.read(3)
        if tag == b"ID3":
            stream.seek(6)
            sizeb = stream.read(4)
            size = (
                (sizeb[0] & 0x7F) << 21
                | (sizeb[1] & 0x7F) << 14
                | (sizeb[2] & 0x7F) << 7
                | (sizeb[3] & 0x7F)
            )
            stream.seek(10 + size)
        # No TAGv2 space
        else:
            stream.seek(0)

        header = stream.read(4)
        if len(header) != 4:
            raise Exception("Invalid Frame Header: Length is not 4 bytes.")

        sync12 = (header[0] << 4) | (header[1] >> 4)
        sync11 = (header[0] << 3) | (header[1] >> 5)

        if (sync11 & 0x7FF) == 0x7FF:
            sync = format(sync11, "011b")

        elif (sync12 & 0xFFE) == 0xFFE:  # Check for 12-bit sync
            sync = format(sync12, "012b")
        else:
            raise Exception("Frame Synchronizer bits are not set to 1 (11 or 12).")

        size = "".join(format(byte, "08b") for byte in header)
        if len(size) != 32:
            raise Exception(f"Header Size is not 32. (size: {size})")

        return (sync, "".join(format(byte, "08b") for byte in header))
