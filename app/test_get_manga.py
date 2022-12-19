import unittest
import  json
from main import get_data_manga

class GetMangaTest(unittest.TestCase):
    def test_get_manga(self):
        test_url = "https://chapmanganato.com/manga-wd951838"
        self.maxDiff = None
        res = get_data_manga(test_url)