from pathlib import Path

from mpegi.frames import Tag


class TestV1:
    def setup_class(self):
        audio = Path("./mp3/imagematerial.mp3")
        tag = Tag(audio)
        self.content = tag.get()

    def test_identifier(self):
        assert self.content[0]["Identifier"] == "TAG"

    def test_title(self):
        assert self.content[0]["Title"] == "IMAGE -MATERIAL- <Version 0>"

    def test_artist(self):
        assert self.content[0]["Artist"] == "Tatsh"

    def test_album(self):
        assert self.content[0]["Album"] == "MATERIAL"

    def test_year(self):
        assert self.content[0]["Year"] == "2011"

    def test_comments(self):
        assert self.content[0]["Comments"] == None

    def test_genre(self):
        assert self.content[0]["Genre"] == "Other"
