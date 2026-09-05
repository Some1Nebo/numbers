"""Opt-in AppKit integration checks: NUMBERS_UI_TESTS=1 python -m unittest ..."""

import os
import contextlib
import io
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

from rep import Rep
from workout import Workout
from workout_template import WorkoutTemplate


@unittest.skipUnless(sys.platform == "darwin" and os.getenv("NUMBERS_UI_TESTS") == "1",
                     "AppKit checks run explicitly on a Mac with a graphical session")
class WorkoutWindowTests(unittest.TestCase):
    def setUp(self):
        from AppKit import NSApplication
        from menubar import NumbersWorkoutApp
        NSApplication.sharedApplication()
        self.tmp = tempfile.TemporaryDirectory()
        with patch.dict(os.environ, {"NUMBERS_WORKOUT_HOME": self.tmp.name}):
            self.app = NumbersWorkoutApp()
        self.store = self.app._store
        self.controller = self.app._window

    def tearDown(self):
        help_window = getattr(self.app, "_help_window", None)
        if help_window is not None:
            help_window.window.close()
        self.controller.window.setDelegate_(None)
        self.controller.window.close()
        self.store.close()
        self.tmp.cleanup()

    def test_help_reopens_one_native_window_without_interrupting_workout(self):
        self.start_fixture()
        self.controller.answer.setStringValue_("12")
        # The old modal helper blocks the test process; reject that boundary.
        with patch("menubar._alert", side_effect=AssertionError("Help must use a native window")):
            self.app.show_help(None)
        help_window = self.app._help_window
        self.assertTrue(help_window.window.isVisible())
        self.assertIsNot(help_window.window, self.controller.window)
        help_window.done_(None)
        self.assertFalse(help_window.window.isVisible())
        self.app.show_help(None)
        self.assertIs(self.app._help_window, help_window)
        self.assertTrue(help_window.window.isVisible())
        self.assertEqual(self.controller.view_name, "workout")
        self.assertEqual(self.controller.session.completed, 0)
        self.assertEqual(self.controller.answer.stringValue(), "12")

    def start_fixture(self):
        with patch("runner.Workout.generate", return_value=Workout([Rep("10 + 2"), Rep("20 + 3")])):
            self.controller.start(WorkoutTemplate.parse("s-a-2"))

    def test_one_window_advances_and_saves_only_at_the_end(self):
        self.controller.show_setup()
        window = self.controller.window
        self.start_fixture()
        self.controller.answer.setStringValue_("12")
        self.controller.submit_(None)
        self.assertEqual(self.store.totals()["sessions"], 0)
        self.assertEqual(self.controller.expression.stringValue(), "20 + 3")
        self.controller.answer.setStringValue_("24")
        self.controller.submit_(None)
        self.assertIs(self.controller.window, window)
        self.assertEqual(self.controller.view_name, "results")
        self.assertEqual(self.store.totals()["sessions"], 1)
        self.assertEqual(self.controller.result.correct, 1)
        self.assertEqual(self.controller.result.answers, ["12", "24"])
        self.controller.submit_(None)  # A late/double Enter cannot save twice.
        self.assertEqual(self.store.totals()["sessions"], 1)

    def test_invalid_input_does_not_advance_but_wrong_integer_does(self):
        self.start_fixture()
        for value in ("", "abc", "12.5"):
            self.controller.answer.setStringValue_(value)
            self.controller.submit_(None)
            self.assertEqual(self.controller.session.completed, 0)
            self.assertTrue(self.controller.error_label.stringValue())
        self.controller.answer.setStringValue_("0")
        self.controller.submit_(None)
        self.assertEqual(self.controller.session.completed, 1)
        self.assertEqual(self.controller.error_label.stringValue(), "")

    def test_custom_setup_validates_and_restores_preferences(self):
        self.controller.show_setup()
        self.controller.rep_count.setStringValue_("0")
        self.controller.startCustom_(None)
        self.assertEqual(self.controller.view_name, "setup")
        self.controller.rep_count.setStringValue_("5")
        for button in self.controller.operation_buttons.values():
            button.setState_(0)
        self.controller.startCustom_(None)
        self.assertEqual(self.controller.view_name, "setup")
        self.controller.operation_buttons["m"].setState_(1)
        self.controller.difficulty.setSelectedSegment_(2)
        self.controller.startCustom_(None)
        self.assertEqual(self.controller.view_name, "workout")
        saved = self.store.last_template()
        self.assertEqual((saved.mode(), saved.rep_types(), saved.num_of_reps()), ("h", {"m"}, 5))

    def test_close_during_workout_requests_confirmation_without_discarding(self):
        self.start_fixture()
        self.controller.answer.setStringValue_("12")
        self.controller.submit_(None)
        self.assertFalse(self.controller.windowShouldClose_(self.controller.window))
        self.assertEqual(self.controller.session.completed, 1)
        self.assertEqual(self.store.totals()["sessions"], 0)
        self.assertIsNotNone(self.controller.window.attachedSheet())

    def test_history_handles_empty_and_populated_database(self):
        self.controller.show_history()
        self.assertEqual(self.controller.view_name, "history")
        self.start_fixture()
        for answer in ("12", "23"):
            self.controller.answer.setStringValue_(answer)
            self.controller.submit_(None)
        self.controller.show_history()
        self.assertEqual(self.controller.view_name, "history")
        self.assertEqual(self.store.totals()["correct"], 2)

    def test_successful_save_retry_reenables_history_and_custom_workout(self):
        self.store._conn.execute(
            "CREATE TRIGGER fail_rep BEFORE INSERT ON session_reps "
            "BEGIN SELECT RAISE(ABORT, 'test save failure'); END")
        self.start_fixture()
        with contextlib.redirect_stderr(io.StringIO()):
            for answer in ("12", "23"):
                self.controller.answer.setStringValue_(answer)
                self.controller.submit_(None)
        self.assertFalse(self.app.history_item._menuitem.isEnabled())
        self.assertEqual(self.store.totals()["sessions"], 0)
        self.store._conn.execute("DROP TRIGGER fail_rep")
        self.controller.retrySave_(None)
        self.assertEqual(self.store.totals()["sessions"], 1)
        self.assertTrue(self.app.history_item._menuitem.isEnabled())
        self.assertTrue(self.app.custom_item._menuitem.isEnabled())

    def test_native_quit_closes_database_before_application_exits(self):
        import rumps

        def native_run(*args, **kwargs):
            # AppKit termination emits before_quit and need not unwind run().
            rumps.events.before_quit.emit()
            with self.assertRaises(sqlite3.ProgrammingError):
                self.store.totals()

        with patch.object(rumps.App, "run", native_run):
            self.app.run()
