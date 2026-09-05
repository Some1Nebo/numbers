import unittest
from rep import *


class RepCreationTests(unittest.TestCase):

    def test_structured_operands_render_math_without_changing_console_format(self):
        rep = Rep(69, "*", 83)
        self.assertEqual((rep.left, rep.operation, rep.right), (69, "*", 83))
        self.assertEqual(str(rep), "69 * 83")
        self.assertEqual(rep.display, "69 × 83")
        self.assertEqual(rep.answer(), 5727)

    def test_rejects_python_expressions_outside_binary_arithmetic(self):
        for expression in ("sum([1, 2])", "2 ** 3", "1 + 2 + 3", "'hello'", "1 / 0"):
            with self.subTest(expression=expression):
                with self.assertRaises(ValueError):
                    Rep(expression)

    def test_division_has_an_exact_integer_answer(self):
        rep = Rep("136 / 8")
        self.assertEqual(rep.answer(), 17)
        self.assertIsInstance(rep.answer(), int)
        self.assertEqual(rep.display, "136 ÷ 8")

    def test_negative_operands_are_preserved(self):
        rep = Rep("-12 - -3")
        self.assertEqual(rep.answer(), -9)
        self.assertEqual(rep.display, "−12 − −3")

    def test_generation_preserves_exact_division_in_every_mode(self):
        for mode in Mode.all():
            for _ in range(20):
                rep = Rep.generate(mode, RepType.DIVISION)
                self.assertIsInstance(rep.answer(), int)
                self.assertEqual(rep.left, rep.right * rep.answer())

    def test_creation_happy_path(self):
        rep_str = "10 * 2"
        rep = Rep(rep_str)

        actual_str = "{0}".format(rep)
        self.assertEqual(actual_str, rep_str)
        self.assertEqual(rep.answer(), 20)

    def test_throws_if_invalid_expression(self):
        self.assertRaises(ValueError, Rep, "10 * (")


if __name__ == "__main__":
    unittest.main()
