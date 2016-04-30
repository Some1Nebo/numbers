import time
from workout_template import *
from workout import *


if __name__ == "__main__":

    default_workout = 'm-*-10'

    print("Hi! What type of a workout are you after? Default: {0}.".format(default_workout))
    workout_str = raw_input()

    if not workout_str or workout_str.isspace():
        workout_str = default_workout

    workout_template = WorkoutTemplate.parse(workout_str)
    workout = Workout.generate(workout_template)

    raw_input("Great! Just press enter when you ready.")

    correct = 0
    wrong_answers = []
    start = time.time()
    for i, rep in enumerate(workout):
        print("({0}) {1}".format(i + 1, rep))

        try:
            answer = int(raw_input())

            if answer == rep.answer():
                correct += 1
            else:
                wrong_answers.append(str(rep))

        except ValueError:
            wrong_answers.append(str(rep))

    end = time.time()

    print("Number of correct answers: {0} ({1}%)".format(correct, correct*100.0/workout_template.num_of_reps()))
    print("Required time: {0}".format(round(end - start, 2)))

    if any(wrong_answers):
        print("Wrong answers:")
        print("\n".join(wrong_answers))

