"""Numbers Workout - macOS menu bar (tray) app.

Run from the source checkout:
    .venv/bin/python menubar.py

The installed app is a PyInstaller-built bundle (see README.md).
"""

import functools
import os
import sys

import rumps
from AppKit import NSAlert, NSApplication, NSImage

from storage import SessionStore
from help_window import HelpWindow
from workout_window import WorkoutWindow
from native_ui import template_description

APP_NAME = "Numbers Workout"


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
            quit_button=None,
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
        self._window = WorkoutWindow.alloc().initWithStore_(self._store)
        self._help_window = None
        self._window.on_change = self._update_menu
        self.start_item = rumps.MenuItem("Start Workout", callback=self.start_workout)
        self.detail_item = rumps.MenuItem("")
        self.custom_item = rumps.MenuItem("Custom Workout…", callback=self.custom_workout)
        self.history_item = rumps.MenuItem("History…", callback=self.show_history)
        self.menu = [
            self.start_item, self.detail_item, self.custom_item, None,
            self.history_item, None,
            rumps.MenuItem("Help", callback=self.show_help),
            rumps.MenuItem("Quit Numbers", callback=self.quit_app),
        ]
        self._update_menu()

    def _update_menu(self):
        busy = self._window.has_pending_work
        self.start_item.title = "Return to Workout" if busy else "Start Workout"
        self.detail_item.title = template_description(self._store.last_template())
        # rumps exposes the underlying NSMenuItem for enabled-state control.
        for item in (self.custom_item, self.history_item):
            item._menuitem.setEnabled_(not busy)

    @_guarded
    def start_workout(self, _sender):
        self._window.start(self._store.last_template())

    @_guarded
    def custom_workout(self, _sender):
        self._window.show_setup()

    @_guarded
    def show_history(self, _sender):
        self._window.show_history()

    @_guarded
    def show_help(self, _sender):
        if self._help_window is None:
            self._help_window = HelpWindow.alloc().init()
        self._help_window.reveal()

    @_guarded
    def quit_app(self, _sender):
        self._window.request_quit(rumps.quit_application)

    def run(self, **options):
        # AppKit can terminate without returning from its event loop.
        rumps.events.before_quit.register(self._store.close)
        try:
            super().run(**options)
        finally:
            rumps.events.before_quit.unregister(self._store.close)
            self._store.close()


def main():
    app = NumbersWorkoutApp()
    if "--setup" in sys.argv:
        # Useful for launching directly into setup, including local UI review.
        rumps.events.before_start.register(lambda: app.custom_workout(None))
    app.run()


if __name__ == "__main__":
    main()
