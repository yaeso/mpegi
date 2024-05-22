from pathlib import Path

from mpegi.metadata import Tag


class TestV1:
    def setup_class(self):
        audio = Path("imagematerial.mp3")
        with Tag(audio) as tag:
            assert tag._v1() != None
            self.content = tag.content_v1()

    def test_identifier(self):
        assert self.content["Identifier"] == "TAG"

    def test_title(self):
        assert self.content["Title"] == "IMAGE -MATERIAL- <Version 0>"

    def test_artist(self):
        assert self.content["Artist"] == "Tatsh"

    def test_album(self):
        assert self.content["Album"] == "MATERIAL"

    def test_year(self):
        assert self.content["Year"] == "2011"

    def test_comments(self):
        assert self.content["Comments"] == None

    def test_genre(self):
        assert self.content["Genre"] == "Other"
