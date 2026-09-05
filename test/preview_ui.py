"""Manual native UI preview with disposable data and a per-window appearance.

Run from the repo root:
    .venv/bin/python test/preview_ui.py --appearance light --scene results

This harness never opens your personal database or changes macOS appearance.
It also provides a long list of mistakes to check scrolling and layout.
"""

import argparse
import os
from pathlib import Path
import sys
import tempfile
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import AppKit as A
import rumps

from menubar import NumbersWorkoutApp
from rep import Rep
from runner import SessionResult
from workout import Workout
from workout_template import WorkoutTemplate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--appearance", choices=("light", "dark"), default="dark")
    parser.add_argument("--scene", choices=("setup", "workout", "results", "history", "help"), default="setup")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="numbers-ui-preview-") as directory:
        os.environ["NUMBERS_WORKOUT_HOME"] = directory
        app = NumbersWorkoutApp()

        def show():
            controller = app._window
            name = A.NSAppearanceNameAqua if args.appearance == "light" else A.NSAppearanceNameDarkAqua
            controller.window.setAppearance_(A.NSAppearance.appearanceNamed_(name))
            if args.scene == "help":
                app.show_help(None)
                app._help_window.window.setAppearance_(A.NSAppearance.appearanceNamed_(name))
            elif args.scene == "setup":
                controller.show_setup()
            elif args.scene == "workout":
                controller.start(WorkoutTemplate.parse("m-*-10"))
            else:
                template = WorkoutTemplate.parse("m-m-20")
                now = datetime.now()
                result = SessionResult(template, Workout([Rep(12 + i, "*", 13) for i in range(20)]),
                                       ["0"] * 20, now, now, 75.0)
                app._store.record_session(result)
                if args.scene == "history":
                    controller.show_history()
                else:
                    controller.result, controller.saved = result, True
                    controller.show_results()
                    controller.reveal()

        rumps.events.before_start.register(show)
        app.run()


if __name__ == "__main__":
    main()
