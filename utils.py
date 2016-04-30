from random import randint, shuffle


def get_randomly_placed_randoms_with_n_digits(num_of_digits_arr):
    operands = [random_with_n_digits_from_range(r) for r in num_of_digits_arr]
    shuffle(operands)
    return operands


def random_with_n_digits_from_range(range_of_digits):
    i = randint(0, len(range_of_digits)-1)
    return random_with_n_digits(range_of_digits[i])


def random_with_n_digits(n):
    range_start = 10**(n-1)+1
    range_end = (10**n)-1
    return randint(range_start, range_end)
