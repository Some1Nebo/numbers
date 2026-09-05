"""SQLite-backed storage for workout sessions.

Database location (macOS per-user app data convention):
    ~/Library/Application Support/numbers-workout/numbers.db

Override the directory with the NUMBERS_WORKOUT_HOME env var (used by tests).

The schema is deliberately flat so an analytics layer can be built on top:
    sessions      - one row per workout session
    session_reps  - one row per rep, with the given answer and whether it was correct
"""

import os
import sqlite3
from collections import namedtuple
from datetime import datetime

from runner import matches_answer
from workout_template import WorkoutTemplate

DEFAULT_TEMPLATE = "m-*-10"

# Read-only summary of a sessions row, as returned by SessionStore.recent_sessions.
SessionSummary = namedtuple(
    "SessionSummary",
    ["id", "finished_at", "template", "correct", "completed_reps", "duration_sec"],
)


def default_db_path():
    base = os.environ.get("NUMBERS_WORKOUT_HOME")
    if not base:
        base = os.path.join(os.path.expanduser("~"), "Library", "Application Support", "numbers-workout")
    return os.path.join(base, "numbers.db")


class SessionStore:

    _SCHEMA = """
    CREATE TABLE IF NOT EXISTS preferences (
        key   TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS sessions (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        started_at     TEXT    NOT NULL,
        finished_at    TEXT    NOT NULL,
        duration_sec   REAL    NOT NULL,
        template       TEXT    NOT NULL,
        mode           TEXT    NOT NULL,
        rep_types      TEXT    NOT NULL,
        num_reps       INTEGER NOT NULL,
        completed_reps INTEGER NOT NULL,
        correct        INTEGER NOT NULL,
        wrong          INTEGER NOT NULL,
        score_pct      REAL
    );

    CREATE TABLE IF NOT EXISTS session_reps (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id     INTEGER NOT NULL REFERENCES sessions (id) ON DELETE CASCADE,
        seq            INTEGER NOT NULL,
        rep            TEXT    NOT NULL,
        given_answer   TEXT,
        correct_answer INTEGER NOT NULL,
        was_correct    INTEGER NOT NULL
    );

    CREATE INDEX IF NOT EXISTS idx_session_reps_session_id ON session_reps (session_id);
    """

    def __init__(self, db_path=None):
        self._db_path = db_path or default_db_path()
        db_dir = os.path.dirname(self._db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._conn = sqlite3.connect(self._db_path)
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._conn.executescript(self._SCHEMA)
        self._conn.commit()

    # ------------------------------------------------------------------- write

    def remember_template(self, template):
        with self._conn:
            self._conn.execute(
                "INSERT INTO preferences (key, value) VALUES ('last_template', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (template.template_str(),))

    def record_session(self, result):
        """Persist a SessionResult (see runner.py). Returns the new session id."""
        template = result.template
        reps = list(result.workout)
        completed = result.completed
        correct = result.correct
        score_pct = correct * 100.0 / completed if completed else None

        with self._conn:
            cur = self._conn.execute(
                """INSERT INTO sessions
                   (started_at, finished_at, duration_sec, template, mode, rep_types,
                    num_reps, completed_reps, correct, wrong, score_pct)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    _iso(result.started_at),
                    _iso(result.finished_at),
                    result.duration.total_seconds(),
                    template.template_str(),
                    template.mode(),
                    ",".join(sorted(template.rep_types())),
                    template.num_of_reps(),
                    completed,
                    correct,
                    result.wrong,
                    score_pct,
                ),
            )
            session_id = cur.lastrowid

            self._conn.executemany(
                """INSERT INTO session_reps
                   (session_id, seq, rep, given_answer, correct_answer, was_correct)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                [
                    (session_id, i, str(rep), answer, rep.answer(), int(matches_answer(rep, answer)))
                    for i, (rep, answer) in enumerate(zip(reps, result.answers), start=1)
                ],
            )
        return session_id

    def clear_history(self):
        """Delete all sessions (their reps go with them, via ON DELETE CASCADE)."""
        self._conn.execute("DELETE FROM sessions")
        self._conn.commit()

    # -------------------------------------------------------------------- read

    def last_template(self):
        row = self._conn.execute(
            "SELECT value FROM preferences WHERE key = 'last_template'").fetchone()
        if row is not None:
            try:
                return WorkoutTemplate.parse(row[0])
            except (ValueError, TypeError):
                pass
        return WorkoutTemplate.parse(DEFAULT_TEMPLATE)

    def recent_sessions(self, limit=5):
        """Most recent sessions, newest first, as SessionSummary namedtuples."""
        rows = self._conn.execute(
            """SELECT id, finished_at, template, correct, completed_reps, duration_sec
               FROM sessions ORDER BY id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
        return [SessionSummary(*row) for row in rows]

    def totals(self):
        row = self._conn.execute(
            """SELECT COUNT(*),
                      COALESCE(SUM(correct), 0),
                      COALESCE(SUM(completed_reps), 0),
                      COALESCE(AVG(score_pct), 0)
               FROM sessions"""
        ).fetchone()
        return {
            "sessions": row[0],
            "correct": row[1],
            "reps": row[2],
            "avg_score_pct": row[3],
        }

    def close(self):
        self._conn.close()


def _iso(dt):
    if isinstance(dt, datetime):
        return dt.astimezone().isoformat(timespec="seconds")
    return dt
