import unittest
from planner.utils import fix_homedepot_url

class TestFixHomeDepotUrl(unittest.TestCase):
    def test_no_change_for_normal_url(self):
        url = "https://homedepot.com/p/Some-Product/12345"
        self.assertEqual(fix_homedepot_url(url), url)

    def test_fix_apionline_url(self):
        url = "https://apionline.homedepot.com/p/Some-Product/12345"
        expected = "https://homedepot.com/p/Some-Product/12345"
        self.assertEqual(fix_homedepot_url(url), expected)

    def test_none_url(self):
        self.assertIsNone(fix_homedepot_url(None))

    def test_empty_url(self):
        self.assertEqual(fix_homedepot_url(""), "")

    def test_url_with_apionline_but_not_homedepot(self):
        url = "https://apionline.example.com/p/Some-Product/12345"
        self.assertEqual(fix_homedepot_url(url), url)

if __name__ == "__main__":
    unittest.main()
