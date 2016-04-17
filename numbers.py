import time
from random import randint


if __name__ == "__main__":

    correct = 0

    start = time.time()

    for i in range(1, 4):
        left = randint(10, 99)
        right = randint(10, 99)

        print("{0} * {1}".format(left, right))
        answer = int(raw_input())

        if left * right == answer:
            correct += 1

    end = time.time()

    print("Number of correct answers: {0}".format(correct))
    print("Required time: {0}".format(round(end - start, 2)))

