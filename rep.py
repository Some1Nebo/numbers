from utils import *


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

    def __init__(self, rep_str):
        self._rep_str = rep_str

        try:
            # using 'eval' is quite a bad approach, but for my internal usage it's fine
            self._answer = eval(rep_str)
        except SyntaxError:
            raise ValueError("Wrong format of the rep: {0}.".format(rep_str))

    def answer(self):
        return self._answer

    def __str__(self):
        return self._rep_str

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
        return Rep("{1} {0} {2}".format(operation, operands[0], operands[1]))
