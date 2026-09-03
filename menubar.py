"""Numbers Workout - macOS menu bar (tray) app.

Run from the source checkout:
    .venv/bin/python menubar.py

The installed app is a PyInstaller-built bundle (see README.md).
"""

import functools
import os
import sys
from datetime import datetime

import rumps
from AppKit import NSAlert, NSApplication, NSImage

from runner import run_workout
from storage import SessionStore
from workout_template import WorkoutTemplate

APP_NAME = "Numbers Workout"
DEFAULT_TEMPLATE = "m-*-10"
_OK_BUTTON = 1  # rumps Response.clicked value for the OK button
# Plain hyphens: box-drawing characters (─) trigger a broken font fallback
# inside NSAlert informative text (verified by offscreen rendering).
_SEPARATOR = "-" * 30


def _resource_path(name):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def _sf_symbol_image():
    """Menu bar icon as a native SF Symbol (crisper than the bundled PNG), or None."""
    for symbol in ("dumbbell", "function", "hash"):
        image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(symbol, APP_NAME)
        if image is not None:
            image.setTemplate_(True)
            return image
    return None


# NSWindowLevel: above normal app windows, below the menu bar and status items.
_FLOATING_WINDOW_LEVEL = 3


def _activate_app():
    """Bring the app to the front.

    Menu-bar-only (LSUIElement) apps are not activated automatically, and
    macOS may refuse activation for a background app, so this alone is not
    enough — modal windows also get a floating window level (see below).
    """
    NSApplication.sharedApplication().activateIgnoringOtherApps_(True)


def _float_window(window_obj):
    """Raise a window so it stays above the user's normal app windows."""
    window_obj.setLevel_(_FLOATING_WINDOW_LEVEL)


def _make_alert(title, message, cancel=False):
    """Build the app's standard NSAlert (no modality) so callers can inspect
    or render it; % is escaped because the text goes through ...WithFormat_.
    """
    return NSAlert.alertWithMessageText_defaultButton_alternateButton_otherButton_informativeTextWithFormat_(
        title, None, "Cancel" if cancel else None, None, str(message).replace("%", "%%"))


def _alert(title, message, cancel=False):
    """_make_alert plus app activation and a floating window level, because a
    plain runModal in a menu-bar-only app can appear behind the user's
    frontmost window and look like the click did nothing.

    Returns the clicked button: 1 for OK, 2 for Cancel.
    """
    _activate_app()
    alert = _make_alert(title, message, cancel)
    _float_window(alert.window())
    return alert.runModal() % 999


def _run_window(window):
    """Run a rumps.Window, activating the app first (see _activate_app)."""
    _activate_app()
    _float_window(window._alert.window())  # rumps keeps the NSAlert in _alert
    return window.run()


def _format_time(iso_str):
    """'2026-09-03T17:45:12+03:00' -> 'Sep 03 17:45'."""
    try:
        return datetime.fromisoformat(iso_str).strftime("%b %d %H:%M")
    except ValueError:
        return iso_str


def _guarded(method):
    """Menu callbacks must not propagate exceptions into the app main loop."""

    @functools.wraps(method)
    def wrapper(self, *args):
        try:
            return method(self, *args)
        except Exception as exc:
            _alert("Something went wrong", str(exc))

    return wrapper


class NumbersWorkoutApp(rumps.App):

    def __init__(self):
        # rumps only accepts a file path for the icon, so start with the bundled PNG.
        super().__init__(
            APP_NAME,
            icon=_resource_path("menubar_icon.png"),
            template=True,
            quit_button="Quit",
        )
        # ...and upgrade to a native SF Symbol when one is available. The internal
        # NSApp delegate reads _icon_nsimage when it builds the status bar in run(),
        # so overwriting it here is enough.
        try:
            symbol_image = _sf_symbol_image()
            if symbol_image is not None:
                self._icon_nsimage = symbol_image
            else:
                print("No SF Symbol available; keeping the bundled PNG icon.", file=sys.stderr)
        except Exception as exc:
            print("Could not use the SF Symbol icon ({0}); keeping the bundled PNG.".format(exc),
                  file=sys.stderr)

        self._store = SessionStore()
        self._current_template = None

        self.start_item = rumps.MenuItem("Start Workout…", callback=self.start_workout)
        self.recent_item = rumps.MenuItem("Recent Sessions", callback=self.show_recent)
        self.stats_item = rumps.MenuItem("All-time Stats", callback=self.show_stats)
        self.help_item = rumps.MenuItem("Help", callback=self.show_help)
        self.clear_item = rumps.MenuItem("Clear History", callback=self.clear_history)

        self.menu = [
            self.start_item, None,
            self.recent_item, self.stats_item,
            None,
            self.help_item, self.clear_item,
        ]

    # ------------------------------------------------------------------- menu

    @_guarded
    def start_workout(self, _sender):
        if self._current_template is not None:  # defensive: the item is disabled during a session
            _alert("Workout in progress", "Please finish or cancel the current workout.")
            return

        tpl_window = rumps.Window(
            title=APP_NAME,
            message="Workout template (default {0}), or press Cancel:".format(DEFAULT_TEMPLATE),
            default_text=DEFAULT_TEMPLATE,
            cancel=True,
            dimensions=(280, 24),
        )
        response = _run_window(tpl_window)
        if response.clicked != _OK_BUTTON:
            return

        template_str = (response.text or "").strip() or DEFAULT_TEMPLATE
        try:
            template = WorkoutTemplate.parse(template_str)
        except ValueError as exc:
            _alert("Workout template", "Could not read the template: {0}".format(exc))
            return

        self._set_busy(True)
        self._current_template = template
        try:
            result = run_workout(template, self._ask_answer)
        finally:
            self._current_template = None
            self._set_busy(False)

        if result.completed < result.template.num_of_reps():
            _alert("Workout cancelled", "Nothing was saved.")
            return

        session_id = self._store.record_session(result)
        self._show_summary(result, session_id)

    def _show_summary(self, result, session_id):
        """End-of-session summary, mirroring the console output."""
        score_pct = result.correct * 100.0 / result.completed if result.completed else 0.0

        lines = [
            "{0}/{1} correct  ({2:.0f}%)".format(result.correct, result.completed, score_pct),
            "Time: {0:.1f}s".format(result.duration.total_seconds()),
        ]
        if result.wrong_reps:
            lines += ["", "Wrong answers:"] + result.wrong_reps
        lines += ["", "Saved as session #{0}".format(session_id)]

        _alert("Workout finished", "\n".join(lines))

    def _ask_answer(self, index, rep_str):
        total = self._current_template.num_of_reps()
        window = rumps.Window(
            title="{0} - {1} of {2}".format(APP_NAME, index, total),
            message="What is:  {0}  ?".format(rep_str),
            cancel=True,
            dimensions=(280, 24),
        )
        response = _run_window(window)
        if response.clicked != _OK_BUTTON:
            return None  # abort the session; nothing will be saved
        return response.text

    def _set_busy(self, busy):
        # rumps 0.4.0 exposes no enabled API for menu items; use the wrapped NSMenuItem.
        for item in (self.start_item, self.recent_item, self.stats_item,
                     self.help_item, self.clear_item):
            item._menuitem.setEnabled_(not busy)

    @_guarded
    def show_recent(self, _sender):
        sessions = self._store.recent_sessions(limit=5)
        if not sessions:
            _alert("Recent Sessions", "No sessions stored yet. Start a workout!")
            return
        lines = [
            "#{0:<3} {1:<13} {2:<7} {3:.0f}s".format(
                session.id, _format_time(session.finished_at),
                "{0}/{1}".format(session.correct, session.completed_reps),
                session.duration_sec)
            for session in sessions
        ]
        _alert("Recent Sessions",
               "Last {0} session(s):\n{1}\n{2}".format(len(sessions), _SEPARATOR, "\n".join(lines)))

    @_guarded
    def show_stats(self, _sender):
        totals = self._store.totals()
        if totals["sessions"] == 0:
            _alert("All-time Stats", "No sessions stored yet. Start a workout!")
            return
        _alert(
            "All-time Stats",
            "{0}\n{1:<12}{2}\n{3:<12}{4}  ({5} correct)\n{6:<12}{7:.1f}%".format(
                _SEPARATOR,
                "Sessions:", totals["sessions"],
                "Reps:", totals["reps"], totals["correct"],
                "Avg score:", totals["avg_score_pct"]),
        )

    @_guarded
    def show_help(self, _sender):
        # Line widths are constrained: the informative field is ~220 pt and
        # leading spaces are trimmed (verified by offscreen rendering).
        _alert(
            "Numbers Workout — Help",
            "Template: {mode}-{types}-{reps}\n\n"
            "s  simple · m  medium · h  hard\n"
            "a  + · s  - · m  * · d  / · *  all\n\n"
            "Examples\n"
            "m-*-10   medium, 10 reps\n"
            "s-a-5    simple +, 5 reps\n"
            "h-m,d-20 hard * and /, 20 reps",
        )

    @_guarded
    def clear_history(self, _sender):
        count = self._store.totals()["sessions"]
        if count == 0:
            _alert("Clear History", "There is no history to clear.")
            return
        clicked = _alert(
            "Clear History",
            "Delete all {0} saved session(s)? This cannot be undone.".format(count),
            cancel=True,
        )
        if clicked != _OK_BUTTON:
            return
        self._store.clear_history()


def main():
    NumbersWorkoutApp().run()


if __name__ == "__main__":
    main()
