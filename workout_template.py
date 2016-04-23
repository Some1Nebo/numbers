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


class WorkoutTemplate:
    WILDCARD = "*"

    def __init__(self, mode, rep_types, num_of_reps):
        self._mode = mode
        self._rep_types = rep_types
        self._num_of_reps = num_of_reps

    def mode(self):
        return self._mode

    def rep_types(self):
        return self._rep_types

    def num_of_reps(self):
        return self._num_of_reps

    @staticmethod
    def parse(template_str):
        """Parse WorkoutTemplate object from the string.
        Args:
            template_str: string with the following format - "{mode}-{rep_types}-{num_of_reps}".
            Example. "s-a,m-10" means that we want a 'simple' mode, with 'addition' and 'multiplication' and 10 reps total

        Returns:
            WorkoutTemplate object
        """

        mode_str, rep_types_str, num_of_reps_str = template_str.split("-")

        mode = WorkoutTemplate._parse_mode(mode_str)
        rep_types = WorkoutTemplate._parse_rep_types(rep_types_str)
        num_of_reps = WorkoutTemplate._parse_num_of_reps(num_of_reps_str)

        return WorkoutTemplate(mode, rep_types, num_of_reps)

    @staticmethod
    def _parse_mode(mode_str):
        if mode_str not in Mode.all():
            raise ValueError("Unknown mode: {0}".format(mode_str))

        return mode_str

    @staticmethod
    def _parse_rep_types(rep_types_str):
        rep_types = set(rep_types_str.split(","))

        if WorkoutTemplate.WILDCARD in rep_types:
            rep_types.remove(WorkoutTemplate.WILDCARD)
            rep_types.update(RepType.all())

        if not all(rep in RepType.all() for rep in rep_types):
            raise ValueError("Unknown reps provided.")

        return rep_types

    @staticmethod
    def _parse_num_of_reps(num_of_reps_str):
        return int(num_of_reps_str)
