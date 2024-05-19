 aned and decoded tags
                self.data[tag] = value
        return self.data


# idk

MP3_CHANNELS = {
    00: "Stereo",
    01: "Joint Stereo",
    10: "Dual",
    11: "Mono (single channel)",
}

JOINT_STEREO_MODE_EXTENSIONS = {
    00: "Intensity Stereo [OFF] -- MS Stereo [Off]",
    01: "Intensity Stereo [ON] -- MS Stereo [Off]",
    10: "Intensity Stereo [OFF] -- MS Stereo [ON]",
    11: "Intensity Stereo [ON] -- MS Stereo [ON]",
}

SAMPLING_RATE_FREQUENCY = {
    00: 44100,  # Hz 44.1kHz
    "01": 48000,  # Hz 48kHz
    "10": 32000,  # Hz 32kHz
    "11": "RESERVED",
}

class Metadata:
    def __init__(self, tags: bytes):
        self.data = {
            "Title": tags[3:33],
            "Artist": tags[33:63],
            "Album": tags[63:93],
            "Year": tags[93:97],
            "Comment": tags[97:126],
            "Genre": tags[127:128],
        }

    def metadata(self):
        if tags[:3].decode() == "TAG":
            for tag, value in self.data.items():
                # Decode to UTF-8 to convert e.g. b'Title' -> 'Title'
                value = value.decode("utf-8")

                if tag == "genre":
                    # Convert to integer
                    genre_number = ord(value)
                    value = GENRES[genre_number]
                    # An example of the entire process
                    # value = \x0c -- ord(value) = 12 -- GENRES[12] = Other
                else:
                    # Remove NULL values and whitespace
                    value = value.replace("\x00", "").strip()

                # Update cle
