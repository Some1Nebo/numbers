import unittest

from rep import Rep
from runner import matches_answer, run_workout
from workout_template import WorkoutTemplate


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
