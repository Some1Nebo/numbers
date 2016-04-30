import random
from rep import Rep


class Workout:

    def __init__(self, reps):
        self._reps = reps

    def __iter__(self):
        return iter(self._reps)

    def __str__(self):
        return "\n".join(self._reps)

    @staticmethod
    def generate(workout_template):

        reps = [Rep.generate(workout_template.mode(),
                             random.choice(tuple(workout_template.rep_types())))
                for _ in range(1, workout_template.num_of_reps()+1)]

        return Workout(reps)