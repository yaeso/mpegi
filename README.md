## mpegi

mpegi is a tool designed to extract comprehensive data from MP3 files. It can retrieve its properties, and extract underlying metadata. Additionally, mpegi supports both ID3v1 and ID3v2 tags.

## Getting Started

This project uses Poetry.

Clone the repository, setup the environment, and install the scripts.
```
$ git clone git@github.com:yaeso/mpegi.git 
$ cd mpegi
$ poetry shell
$ poetry install
```
This project does not use any external libraries other than pytest.

## Info

Extract the properties of an MP3 with the `Info` class. If used within a file, enter the MP3 as a `Path`.
```
$ poetry run info --audio /path/to/mp3
```
```
File Name: kotov.mp3
MIME Type: audio/mpeg
File Extension: .mp3
File Size: 7596439 bytes
File Size (mb): 7.24 mb
RFC: 3003
```

## Metadata

Extracts the metadata of an MP3. This includes the Sync, MPEG Version ID, Layer, CRC (Error) Protection, Bit Rate, Sample Rate (Frequency), Padding, Channel (Mode), Mode Extension (if Joint Stereo), Copyright, Original, Emphasis, and Frame Length.
```
$ poetry run metadata --audio /path/to/mp3
```
```
Example output:

  Version         MPEG Version 1 (ISO/IEC 11172-3)
  Layer           Layer III
  CRC             1
  Bitrate         192
  Sample Rate     44100
  Padding         0
  Private         0
  Channel         ('Joint Stereo', 'Intensity Stereo [OFF] -- MS Stereo [ON]')
  Copyright       0
  Original        1
  Emphasis        None
  Frame Length    626
```

## Tags

Extracts contents from both TAGV1 and TAGV2 data spaces. If either tag space does not exist, an `MP3 does not contain a TAGv<version> space.` exception is raised.

Simply use:
```
$ poetry run tag --audio /path/to/mp3 

If you want to save images when an APIC tag is present, pass in --save-image

$ poetry run tag --audio /path/to/mp3 --save-image
```

### TAGV1

TAGV1 has a very simple structure. It always takes up 128 bytes at the very end of the file.
```txt
Bytes     Length      Content 
0-2       3           Tag identifier. Must contain a "TAG" string.
3-32      30          Song Name
33-62     30          Artist
63-92     30          Album
93-96     4           Year
97-126    30          Comment
127       1           Genre
```
Although the 126th byte can sometimes be used to store the track number, I have decided to ignore it.

Genre is stored as an integer that maps to a specific genre. Check `genres.py` or see: https://en.wikipedia.org/wiki/List_of_ID3v1_genres

### TAGV2 

TAGV2 has a much more complicated structure. This tag appears at the very start of the audio file. It contains a main header followed by frames storing information. 

The header is 10 bytes and contains the following structure:
```
Bytes     Content
0-2       TAG identifier. Must contain a "ID3" string.
3-4       TAG version. E.g. 03 00 == ID3v2.3.0
5         Flags
6-9       Size of TAG
```
Flags is a single byte where the first 4 bits corresponds to Unsynchronization, Extended Header, Experimental Indicator, and Footer Present.

See 3.1: https://id3.org/id3v2.4.0-structure

After going through all of this, the frames that follow are parsed for their information and returned in a tuple.
```py
# Most tags will have a format of..
(
  "TIT2",
  "Title"
)

# Some may look like..
(
  "TXXX",
  (
    "Description",
    "Value/Text"
  )
)

# The rest are rather unique..
(
  "APIC",
  (
    "MIME Type",
    "Picture Type",
    "Description"
  )
)

```
All metadata is then stored in a dictionary and returned.

## Restrictions

A few of the ID3 tags are not implemented as of yet. The tags not implemented will return `Not Implemented`. These include USLT, SYTC, MLLT, ETOC, RVA2, EQU2, RVRB, PCNT, POPM, RBUF, AENC, LINK, POSS, USER, OWNE, COMR, ENCR, GRID, PRIV, SIGN, SEEK, ASPI, and the 2.2 tags. 

See: https://exiftool.org/TagNames/ID3.html

## References

ID3v2.3.0

  > Martin Nilsson, [https://id3.org/id3v2.3.0](id3)

ID3v2.4.0

  > Martin Nilsson, [https://id3.org/id3v2.4.0-structure](id3)

ID3v2.4.0 Frames

  > Martin Nilsson, [https://mutagen-specs.readthedocs.io/en/latest/id3/id3v2.4.0-frames.html](mutagen)

MP3 File structure

  > [https://en.wikipedia.org/wiki/MP3#File_structure](Wikipedia)

  > [http://www.multiweb.cz/twoinches/mp3inside.htm#FrameHeaderE](multiweb)

ID3 Tag Names 

  > [https://exiftool.org/TagNames/ID3.html](exiftool)

File Signatures

  > [https://en.wikipedia.org/wiki/List_of_file_signatures](Wikipedia)

Frame Header Information 

  > [http://mpgedit.org/mpgedit/mpeg_format/MP3Format.html](mpgedit)

  > [http://www.mp3-tech.org/programmer/frame_header.html](mp3-tech)


Beat Detection

  > [https://archive.gamedev.net/archive/reference/programming/features/beatdetection/](gamedev)

  > G. Tzanetakis, G. Essl and P. Cook, [https://soundlab.cs.princeton.edu/publications/2001_amta_aadwt.pdf]



