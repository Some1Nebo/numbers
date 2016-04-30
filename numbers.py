import time
from workout_template import *
from workout import *


if __name__ == "__main__":

    default_workout = 'm-*-10'

    print("Hi! What type of workout are you after? Default: {0}.".format(default_workout))

    workout_str = raw_input()

    if not workout_str or workout_str.isspace():
        workout_str = default_workout

    workout_template = WorkoutTemplate.parse(workout_str)
    workout = Workout.generate(workout_template)

    start = time.time()

    correct = 0
    for rep in workout:
        print(rep)
        answer = int(raw_input())

        if answer == rep.answer():
            correct += 1

    end = time.time()

    print("Number of correct answers: {0} ({1}%)".format(correct, correct*100.0/workout_template.num_of_reps()))
    print("Required time: {0}".format(round(end - start, 2)))

