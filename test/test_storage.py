import os
import tempfile
import unittest

from runner import run_workout
from storage import SessionStore
from workout_template import WorkoutTemplate


class SessionStoreTests(unittest.TestCase):

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self._store = SessionStore(os.path.join(self._tmp.name, "test.db"))

    def tearDown(self):
        self._store.close()
        self._tmp.cleanup()

    def _record(self, template_str, ask=None):
        if ask is None:
            ask = lambda index, rep_str: str(eval(rep_str))
        template = WorkoutTemplate.parse(template_str)
        return self._store.record_session(run_workout(template, ask))

    def test_record_and_read_back(self):
        session_id = self._record("m-a,m-3")

        sessions = self._store.recent_sessions(limit=5)
        self.assertEqual(len(sessions), 1)
        session = sessions[0]
        self.assertEqual(session.id, session_id)
        self.assertEqual(session.template, "m-a,m-3")
        self.assertEqual(session.correct, 3)
        self.assertEqual(session.completed_reps, 3)
        self.assertGreaterEqual(session.duration_sec, 0)

    def test_partial_session(self):
        def ask(index, rep_str):
            if index == 3:
                return None
            return str(eval(rep_str)) if index == 1 else "definitely wrong"

        session_id = self._record("s-a-3", ask=ask)

        session = self._store.recent_sessions(limit=5)[0]
        self.assertEqual(session.id, session_id)
        self.assertEqual(session.completed_reps, 2)
        self.assertEqual(session.correct, 1)

    def test_recent_sessions_orders_newest_first_and_limits(self):
        self._record("s-a-1")
        first_id = self._store.recent_sessions(limit=1)[0].id
        self._record("m-a-1")

        sessions = self._store.recent_sessions(limit=1)
        self.assertEqual(len(sessions), 1)
        self.assertNotEqual(sessions[0].id, first_id)

    def test_totals(self):
        self._record("s-a-2")

        totals = self._store.totals()
        self.assertEqual(totals["sessions"], 1)
        self.assertEqual(totals["reps"], 2)
        self.assertEqual(totals["correct"], 2)
        self.assertAlmostEqual(totals["avg_score_pct"], 100.0)

    def test_clear_history(self):
        self._record("s-a-1")
        self._record("m-a-1")

        self._store.clear_history()

        self.assertEqual(len(self._store.recent_sessions(limit=5)), 0)
        self.assertEqual(self._store.totals()["sessions"], 0)


if __name__ == "__main__":
    unittest.main()
