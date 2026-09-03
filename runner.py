"""Shared workout execution logic used by both the console app and the menu bar app."""

from dataclasses import dataclass
from datetime import datetime

from workout import Workout
from workout_template import WorkoutTemplate


@dataclass
class SessionResult:
    template: WorkoutTemplate
    workout: Workout
    answers: list         # raw answer strings, one per rep that was asked
    started_at: datetime
    finished_at: datetime

    @property
    def duration(self):
        return self.finished_at - self.started_at

    @property
    def completed(self):
        return len(self.answers)

    @property
    def correct(self):
        return sum(1 for rep, answer in zip(self.workout, self.answers) if matches_answer(rep, answer))

    @property
    def wrong(self):
        return self.completed - self.correct

    @property
    def wrong_reps(self):
        return [str(rep) for rep, answer in zip(self.workout, self.answers)
                if not matches_answer(rep, answer)]


def run_workout(template, ask_answer):
    """Generate and run a workout, rep by rep.

    :param template: a parsed WorkoutTemplate.
    :param ask_answer: callable(index, rep_str) -> str | None.
        index is 1-based. Return None to abort the session early
        (reps that were already asked are kept in the result).
    :returns: SessionResult
    """
    workout = Workout.generate(template)
    started_at = datetime.now()

    answers = []
    for i, rep in enumerate(workout, start=1):
        answer = ask_answer(i, str(rep))
        if answer is None:
            break
        answers.append(answer)

    finished_at = datetime.now()
    return SessionResult(template, workout, answers, started_at, finished_at)


def matches_answer(rep, answer):
    """True if the raw user answer is an integer equal to the rep's answer."""
    try:
        return int(answer) == rep.answer()
    except (TypeError, ValueError):
        return False
