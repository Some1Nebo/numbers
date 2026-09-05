import unittest
from unittest.mock import patch

from rep import Rep
from runner import matches_answer, run_workout
from workout_template import WorkoutTemplate
from workout import Workout
import runner


class WorkoutSessionTests(unittest.TestCase):

    def session(self):
        self.assertTrue(hasattr(runner, "WorkoutSession"), "An event-driven session is needed")
        return runner.WorkoutSession(
            WorkoutTemplate.parse("s-a-2"), Workout([Rep("10 + 2"), Rep("20 + 3")]))

    def test_progression_and_final_score_keep_raw_answers(self):
        session = self.session()
        self.assertEqual(session.current_rep.answer(), 12)
        session.submit("12")
        self.assertFalse(session.is_complete)
        self.assertEqual(session.current_rep.answer(), 23)
        session.submit("24")
        self.assertTrue(session.is_complete)
        self.assertIsNone(session.current_rep)
        result = session.finish()
        self.assertEqual(result.answers, ["12", "24"])
        self.assertEqual((result.correct, result.wrong), (1, 1))

    def test_aborting_keeps_partial_snapshot_and_seals_session(self):
        session = self.session()
        session.submit("12")
        result = session.finish()
        self.assertEqual(result.completed, 1)
        self.assertIs(session.finish(), result)
        with self.assertRaises(RuntimeError):
            session.submit("23")

    def test_extra_submission_cannot_overwrite_completed_workout(self):
        session = self.session()
        session.submit("12")
        session.submit("23")
        with self.assertRaises(RuntimeError):
            session.submit("99")
        self.assertEqual(session.finish().answers, ["12", "23"])

    def test_duration_uses_monotonic_time_and_stops_at_finish(self):
        with patch("runner.monotonic", side_effect=[100.0, 107.5], create=True):
            session = self.session()
            result = session.finish()
        self.assertEqual(result.duration.total_seconds(), 7.5)


class MatchesAnswerTests(unittest.TestCase):

    def test_correct_answer(self):
        rep = Rep("10 * 2")
        self.assertTrue(matches_answer(rep, "20"))

    def test_wrong_answer(self):
        rep = Rep("10 * 2")
        self.assertFalse(matches_answer(rep, "18"))

    def test_non_numeric_and_missing_answers(self):
        rep = Rep("10 * 2")
        self.assertFalse(matches_answer(rep, "abc"))
        self.assertFalse(matches_answer(rep, ""))
        self.assertFalse(matches_answer(rep, None))


class RunWorkoutTests(unittest.TestCase):

    def test_all_answers_correct(self):
        template = WorkoutTemplate.parse("s-a-3")
        result = run_workout(template, lambda index, rep_str: str(eval(rep_str)))

        self.assertEqual(result.completed, 3)
        self.assertEqual(result.correct, 3)
        self.assertEqual(result.wrong, 0)
        self.assertEqual(result.wrong_reps, [])

    def test_wrong_and_non_numeric_answers(self):
        template = WorkoutTemplate.parse("s-a-2")

        def ask(index, rep_str):
            return "nope" if index == 1 else str(eval(rep_str))

        result = run_workout(template, ask)

        self.assertEqual(result.completed, 2)
        self.assertEqual(result.correct, 1)
        self.assertEqual(result.wrong, 1)
        self.assertEqual(len(result.wrong_reps), 1)

    def test_abort_on_none_keeps_answers_so_far(self):
        template = WorkoutTemplate.parse("s-a-4")
        asked = []

        def ask(index, rep_str):
            asked.append(index)
            if index == 2:
                return None
            return str(eval(rep_str))

        result = run_workout(template, ask)

        self.assertEqual(asked, [1, 2])
        self.assertEqual(result.completed, 1)
        self.assertEqual(result.correct, 1)
        self.assertGreaterEqual(result.duration.total_seconds(), 0)


if __name__ == "__main__":
    unittest.main()
