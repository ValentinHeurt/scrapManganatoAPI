import unittest
import  json
from main import get_genres

class GetGenresTest(unittest.TestCase):
    def test_get_genres(self):
        f = open('./Config/genres.json')
        wanted = json.load(f)
        self.maxDiff = None
        res = get_genres()
        self.assertEqual(res,wanted)