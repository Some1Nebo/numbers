import os
import sqlite3
from contextlib import closing
import tempfile
import unittest

from runner import run_workout
from storage import SessionStore
from workout_template import WorkoutTemplate


class SessionStoreTests(unittest.TestCase):

    def test_legacy_database_keeps_existing_history_when_preferences_are_added(self):
        path = os.path.join(self._tmp.name, "legacy.db")
        # The original two-table schema, before remembered workout preferences.
        with closing(sqlite3.connect(path)) as legacy:
            legacy.executescript("""
                CREATE TABLE sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    started_at TEXT NOT NULL, finished_at TEXT NOT NULL,
                    duration_sec REAL NOT NULL, template TEXT NOT NULL,
                    mode TEXT NOT NULL, rep_types TEXT NOT NULL,
                    num_reps INTEGER NOT NULL, completed_reps INTEGER NOT NULL,
                    correct INTEGER NOT NULL, wrong INTEGER NOT NULL, score_pct REAL
                );
                CREATE TABLE session_reps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    seq INTEGER NOT NULL, rep TEXT NOT NULL, given_answer TEXT,
                    correct_answer INTEGER NOT NULL, was_correct INTEGER NOT NULL
                );
                INSERT INTO sessions VALUES (
                    1, '2026-09-01T12:00:00+03:00', '2026-09-01T12:00:10+03:00',
                    10, 's-a-1', 's', 'a', 1, 1, 1, 0, 100);
                INSERT INTO session_reps VALUES (1, 1, 1, '12 + 13', '25', 25, 1);
            """)
        upgraded = SessionStore(path)
        try:
            self.assertEqual(upgraded.recent_sessions()[0].correct, 1)
            self.assertEqual(upgraded.last_template().template_str(), "m-*-10")
            upgraded.remember_template(WorkoutTemplate.parse("m-m-20"))
            self.assertEqual(upgraded._conn.execute(
                "SELECT rep, given_answer, correct_answer FROM session_reps").fetchall(),
                [("12 + 13", "25", 25)])
            self.assertEqual(upgraded.totals()["sessions"], 1)
        finally:
            upgraded.close()

    def test_failed_save_rolls_back_before_retry(self):
        self._store._conn.execute(
            "CREATE TRIGGER fail_rep BEFORE INSERT ON session_reps "
            "BEGIN SELECT RAISE(ABORT, 'disk test'); END")
        result = run_workout(WorkoutTemplate.parse("s-a-1"), lambda i, rep: "0")
        with self.assertRaises(sqlite3.IntegrityError):
            self._store.record_session(result)
        self.assertEqual(self._store.totals()["sessions"], 0)
        self._store._conn.execute("DROP TRIGGER fail_rep")
        self._store.record_session(result)
        self.assertEqual(self._store.totals()["sessions"], 1)

    def test_remembers_workout_across_reopens_without_creating_a_session(self):
        self.assertTrue(hasattr(self._store, "remember_template"), "Save custom workout preferences")
        self._store.remember_template(WorkoutTemplate.parse("h-m,d-20"))
        other = SessionStore(os.path.join(self._tmp.name, "test.db"))
        try:
            self.assertEqual(other.last_template().template_str(), "h-m,d-20")
            self.assertEqual(other.totals()["sessions"], 0)
            other.clear_history()
            self.assertEqual(other.last_template().template_str(), "h-m,d-20")
        finally:
            other.close()

    def test_no_preference_uses_default_workout(self):
        self.assertTrue(hasattr(self._store, "last_template"), "Read default workout preferences")
        self.assertEqual(self._store.last_template().template_str(), "m-*-10")

    def test_invalid_saved_preference_falls_back_to_default(self):
        self.assertTrue(hasattr(self._store, "last_template"), "Validate saved workout preferences")
        self._store._conn.execute(
            "INSERT INTO preferences (key, value) VALUES ('last_template', 'broken')")
        self._store._conn.commit()
        self.assertEqual(self._store.last_template().template_str(), "m-*-10")

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
