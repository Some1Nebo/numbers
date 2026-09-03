"""Console front-end for Numbers Workout (see README.md for usage)."""

import sys

from runner import run_workout
from storage import SessionStore
from workout_template import WorkoutTemplate

DEFAULT_WORKOUT = 'm-*-10'


def console_ask(index, rep_str):
    print("({0}) {1}".format(index, rep_str))
    return input()


def main():
    print("Hi! What type of a workout are you after? Default: {0}.".format(DEFAULT_WORKOUT))
    workout_str = input()

    if not workout_str or workout_str.isspace():
        workout_str = DEFAULT_WORKOUT

    try:
        workout_template = WorkoutTemplate.parse(workout_str)
    except ValueError as exc:
        print("Sorry, could not read that template: {0}".format(exc))
        print("Expected format: {{mode}}-{{rep_types}}-{{num_of_reps}}, e.g. {0}.".format(DEFAULT_WORKOUT))
        sys.exit(1)

    input("Great! Just press enter when you ready.")

    store = SessionStore()
    try:
        result = run_workout(workout_template, console_ask)
        session_id = store.record_session(result)
    finally:
        store.close()

    print("Number of correct answers: {0} ({1}%)".format(
        result.correct, result.correct * 100.0 / workout_template.num_of_reps()))
    print("Required time: {0}".format(round(result.duration.total_seconds(), 2)))

    if result.wrong_reps:
        print("Wrong answers:")
        print("\n".join(result.wrong_reps))

    print("Saved as session #{0}".format(session_id))


if __name__ == "__main__":
    main()
