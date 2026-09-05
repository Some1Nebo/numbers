"""Shared workout execution logic used by both the console app and the menu bar app."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from time import monotonic

from workout import Workout
from workout_template import WorkoutTemplate


@dataclass
class SessionResult:
    template: WorkoutTemplate
    workout: Workout
    answers: list         # raw answer strings, one per rep that was asked
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float | None = None

    @property
    def duration(self):
        if self.elapsed_seconds is not None:
            return timedelta(seconds=self.elapsed_seconds)
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


class WorkoutSession:
    """Framework-independent session advanced by either UI events or console input.

    Finishing seals a snapshot, including on cancellation. The caller decides
    whether a partial session should be saved; the Mac UI saves complete ones only.
    """

    def __init__(self, template, workout=None):
        self.template = template
        self.workout = workout if workout is not None else Workout.generate(template)
        self._reps = tuple(self.workout)
        self._answers = []
        self._started_at = datetime.now()
        self._started_clock = monotonic()
        self._result = None

    @property
    def completed(self):
        return len(self._answers)

    @property
    def is_complete(self):
        return self.completed == len(self._reps)

    @property
    def current_rep(self):
        return None if self.is_complete else self._reps[self.completed]

    def submit(self, answer):
        if self._result is not None or self.is_complete:
            raise RuntimeError("This workout has already ended.")
        self._answers.append(answer)

    def finish(self):
        if self._result is None:
            self._result = SessionResult(
                self.template, self.workout, self._answers.copy(),
                self._started_at, datetime.now(), monotonic() - self._started_clock)
        return self._result


def run_workout(template, ask_answer):
    """Generate and run a workout, rep by rep.

    :param template: a parsed WorkoutTemplate.
    :param ask_answer: callable(index, rep_str) -> str | None.
        index is 1-based. Return None to abort the session early
        (reps that were already asked are kept in the result).
    :returns: SessionResult
    """
    session = WorkoutSession(template)
    while not session.is_complete:
        answer = ask_answer(session.completed + 1, str(session.current_rep))
        if answer is None:
            break
        session.submit(answer)
    return session.finish()


def matches_answer(rep, answer):
    """True if the raw user answer is an integer equal to the rep's answer."""
    try:
        return int(answer) == rep.answer()
    except (TypeError, ValueError):
        return False
