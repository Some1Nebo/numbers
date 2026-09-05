"""Integer arithmetic exercises, stored as operands rather than executable text."""

import operator
import re

from utils import (
    get_randomly_placed_randoms_with_n_digits,
    random_with_n_digits,
    random_with_n_digits_from_range,
)


class Mode:
    SIMPLE = "s"
    MEDIUM = "m"
    HARD = "h"

    @staticmethod
    def all():
        return {Mode.SIMPLE, Mode.MEDIUM, Mode.HARD}


class RepType:
    ADDITION = "a"
    SUBTRACTION = "s"
    MULTIPLICATION = "m"
    DIVISION = "d"

    @staticmethod
    def all():
        return {RepType.ADDITION, RepType.SUBTRACTION, RepType.MULTIPLICATION, RepType.DIVISION}


class Rep:

    _OPERATIONS = {"+": operator.add, "-": operator.sub,
                   "*": operator.mul, "/": operator.floordiv}
    _DISPLAY_SYMBOLS = str.maketrans({"*": "×", "/": "÷", "-": "−"})

    def __init__(self, left, operation=None, right=None):
        # Retain the original Rep("10 * 2") API for callers and saved exercises.
        if operation is None:
            match = re.fullmatch(r"\s*([+-]?\d+)\s*([+*/-])\s*([+-]?\d+)\s*", str(left))
            if match is None:
                raise ValueError(f"Wrong format of the rep: {left}.")
            left, operation, right = match.groups()
            left, right = int(left), int(right)
        if not isinstance(left, int) or not isinstance(right, int) or operation not in self._OPERATIONS:
            raise ValueError("An exercise needs two integer operands and +, -, * or /.")
        if operation == "/" and (right == 0 or left % right):
            raise ValueError("Division exercises must have an exact integer answer.")
        self.left, self.operation, self.right = left, operation, right

    def answer(self):
        return self._OPERATIONS[self.operation](self.left, self.right)

    def __str__(self):
        return f"{self.left} {self.operation} {self.right}"

    @property
    def display(self):
        return str(self).translate(self._DISPLAY_SYMBOLS)

    @staticmethod
    def generate(mode, rep_type):
        generators = Rep._prepare_generators()
        generator = generators[rep_type]
        return generator(mode)

    @staticmethod
    def _prepare_generators():
        d = dict([(RepType.ADDITION, Rep._gen_addition),
                  (RepType.SUBTRACTION, Rep._gen_subtraction),
                  (RepType.MULTIPLICATION, Rep._gen_multiplication),
                  (RepType.DIVISION, Rep._gen_division)])
        return d

    @staticmethod
    def _gen_addition(mode):
        operands = {
            Mode.SIMPLE: [random_with_n_digits(2), random_with_n_digits(2)],
            Mode.MEDIUM: get_randomly_placed_randoms_with_n_digits([range(2, 5), [3]]),
            Mode.HARD: get_randomly_placed_randoms_with_n_digits([range(4, 6), [4]])
        }[mode]

        return Rep._gen_binary_rep(operands, "+")

    @staticmethod
    def _gen_subtraction(mode):
        operands = {
            Mode.SIMPLE: [random_with_n_digits(2), random_with_n_digits(2)],
            Mode.MEDIUM: get_randomly_placed_randoms_with_n_digits([range(2, 5), [3]]),
            Mode.HARD: get_randomly_placed_randoms_with_n_digits([range(4, 6), [4]])
        }[mode]

        return Rep._gen_binary_rep(operands, "-")

    @staticmethod
    def _gen_multiplication(mode):
        operands = {
            Mode.SIMPLE: get_randomly_placed_randoms_with_n_digits([[1], [2]]),
            Mode.MEDIUM: [random_with_n_digits(2), random_with_n_digits(2)],
            Mode.HARD: get_randomly_placed_randoms_with_n_digits([[3], range(2, 4)])
        }[mode]

        return Rep._gen_binary_rep(operands, "*")

    @staticmethod
    def _gen_division(mode):
        operands = {
            Mode.SIMPLE: get_randomly_placed_randoms_with_n_digits([[1], [2]]),
            Mode.MEDIUM: [random_with_n_digits_from_range(range(1, 3)), random_with_n_digits_from_range(range(2, 4))],
            Mode.HARD: get_randomly_placed_randoms_with_n_digits([range(2, 4), [3]])
        }[mode]

        return Rep._gen_binary_rep([operands[0] * operands[1], operands[0]], "/")

    @staticmethod
    def _gen_binary_rep(operands, operation):
        return Rep(operands[0], operation, operands[1])
