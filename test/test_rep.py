import unittest
from rep import *


class RepCreationTests(unittest.TestCase):

    def test_creation_happy_path(self):
        rep_str = "10 * 2"
        rep = Rep(rep_str)

        actual_str = "{0}".format(rep)
        self.assertEquals(actual_str, rep_str)
        self.assertEquals(rep.get_answer(), 20)

    def test_throws_if_invalid_expression(self):
        self.assertRaises(ValueError, Rep, "10 * (")


if __name__ == "__main__":
    unittest.main()