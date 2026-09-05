"""Persistent native setup, workout, results, and history window.

Only this controller knows AppKit. WorkoutSession owns answer progression,
SessionStore owns persistence, and native_ui owns control styling.
"""

import functools
import sqlite3
import traceback
from datetime import datetime

import AppKit as A
import objc

from native_ui import (
    MODES, OPERATIONS, branded_content, button, card, create_window, duration_text,
    frame, install_application_menu, label, reveal_window, scroll_content, template_description,
)
from runner import WorkoutSession, matches_answer
from workout_template import WorkoutTemplate


def action(method):
    """Do not let Python exceptions escape an Objective-C action callback."""
    @functools.wraps(method)
    def guarded(self, sender):
        try:
            return method(self, sender)
        except Exception as exc:
            traceback.print_exc()
            self.show_error(f"Something went wrong: {exc}")
    return guarded


class WorkoutWindow(A.NSObject):
    def initWithStore_(self, store):
        self = objc.super(WorkoutWindow, self).init()
        if self is None:
            return None
        self.store = store
        self.session = None
        self.result = None
        self.saved = False
        self.view_name = None
        self.on_change = None
        self._sheet = None
        self.window = create_window("Numbers Workout")
        self.window.setDelegate_(self)
        install_application_menu(self)
        return self

    @objc.python_method
    def reveal(self):
        reveal_window(self.window)

    @objc.python_method
    def _view(self, name):
        self.view_name = name
        self.root = branded_content()
        self.window.setContentView_(self.root)
        self.window.setDefaultButtonCell_(None)
        self.error_label = label(self.root, "", 32, 427, 456, 42, size=12)
        self.error_label.setTextColor_(A.NSColor.systemRedColor())

    @objc.python_method
    def show_error(self, message):
        self.error_label.setStringValue_(message)

    @objc.python_method
    def _changed(self):
        if self.on_change is not None:
            self.on_change()

    @property
    def has_pending_work(self):
        return self.session is not None or (self.result is not None and not self.saved)

    @objc.python_method
    def request_quit(self, callback):
        if self.session is not None:
            self.reveal()
            self._confirm_end(callback)
        elif self.result is not None and not self.saved:
            self.reveal()
            self._confirm_discard(callback)
        else:
            callback()

    @objc.python_method
    def show_setup(self):
        if self.has_pending_work or self._sheet is not None:
            self.reveal()
            return
        self._view("setup")
        template = self.store.last_template()
        label(self.root, "A little mental gymnastics.", 32, 62, 456, 40, size=28, bold=True)
        label(self.root, "Make this workout yours.", 32, 108, 456, secondary=True)
        label(self.root, "Difficulty", 32, 154, 456, bold=True)
        self.difficulty = A.NSSegmentedControl.alloc().initWithFrame_(frame(self.root, 32, 181, 456, 34))
        self.difficulty.setSegmentCount_(3)
        self.difficulty.setTrackingMode_(A.NSSegmentSwitchTrackingSelectOne)
        self.difficulty.setControlSize_(A.NSControlSizeLarge)
        for index, (key, title) in enumerate(MODES):
            self.difficulty.setLabel_forSegment_(title, index)
            self.difficulty.setWidth_forSegment_(148, index)
            if key == template.mode():
                self.difficulty.setSelectedSegment_(index)
        self.difficulty.setAccessibilityLabel_("Difficulty")
        self.root.addSubview_(self.difficulty)
        label(self.root, "Operations", 32, 241, 456, bold=True)
        self.operation_buttons = {}
        for index, (key, symbol, title) in enumerate(OPERATIONS):
            control = button(self.root, symbol, self, "operationChanged:", 32 + index * 117, 268, 105, 40)
            control.setButtonType_(A.NSButtonTypePushOnPushOff)
            control.setFont_(A.NSFont.systemFontOfSize_(22))
            control.setState_(1 if key in template.rep_types() else 0)
            control.setAccessibilityLabel_(title)
            control.setToolTip_(title)
            self.operation_buttons[key] = control
        label(self.root, "Length", 32, 339, 456, bold=True)
        self.rep_count = A.NSTextField.alloc().initWithFrame_(frame(self.root, 32, 368, 92, 32))
        self.rep_count.setStringValue_(str(template.num_of_reps()))
        self.rep_count.setFont_(A.NSFont.systemFontOfSize_(18))
        self.rep_count.setAlignment_(A.NSTextAlignmentCenter)
        self.rep_count.setAccessibilityLabel_("Number of questions")
        self.root.addSubview_(self.rep_count)
        label(self.root, "questions", 138, 374, 200, secondary=True)
        button(self.root, "Cancel", self, "done:", 26, 480, 100)
        button(self.root, "Start Workout", self, "startCustom:", 324, 480, 170, primary=True)
        self.reveal()
        self.window.makeFirstResponder_(self.difficulty)

    @action
    def operationChanged_(self, sender):
        self.show_error("")

    @action
    def startCustom_(self, sender):
        count_text = self.rep_count.stringValue().strip()
        try:
            count = int(count_text)
            if not 1 <= count <= 1000:
                raise ValueError
        except ValueError:
            self.show_error("Choose a whole number of questions between 1 and 1,000.")
            self.window.makeFirstResponder_(self.rep_count)
            return
        operations = {key for key, control in self.operation_buttons.items() if control.state()}
        if not operations:
            self.show_error("Choose at least one operation.")
            return
        mode = MODES[self.difficulty.selectedSegment()][0]
        self.start(WorkoutTemplate(mode, operations, count))

    @objc.python_method
    def start(self, template):
        if self.has_pending_work or self._sheet is not None:
            self.reveal()
            return
        self.store.remember_template(template)
        self.session = WorkoutSession(template)
        self.result, self.saved = None, False
        self._view("workout")
        self.progress_label = label(self.root, "", 332, 23, 156, size=13, secondary=True)
        self.progress_label.setAlignment_(A.NSTextAlignmentRight)
        label(self.root, template_description(template), 32, 78, 456, secondary=True, center=True)
        self.progress = A.NSProgressIndicator.alloc().initWithFrame_(frame(self.root, 32, 116, 456, 4))
        self.progress.setIndeterminate_(False)
        self.progress.setMinValue_(0)
        self.progress.setMaxValue_(template.num_of_reps())
        self.progress.setAccessibilityLabel_("Workout progress")
        self.root.addSubview_(self.progress)
        self.expression = label(self.root, "", 24, 175, 472, 68, size=48, bold=True, center=True)
        card(self.root, 100, 283, 320, 68)
        self.answer = A.NSTextField.alloc().initWithFrame_(frame(self.root, 116, 296, 288, 46))
        self.answer.setFont_(A.NSFont.monospacedDigitSystemFontOfSize_weight_(30, A.NSFontWeightRegular))
        self.answer.setAlignment_(A.NSTextAlignmentCenter)
        self.answer.setBezeled_(False)
        self.answer.setDrawsBackground_(False)
        self.answer.setPlaceholderString_("Your answer")
        self.answer.setAccessibilityLabel_("Your answer")
        self.answer.setTarget_(self)
        self.answer.setAction_("submit:")
        self.root.addSubview_(self.answer)
        label(self.root, "Take your time. Press Return to continue.", 32, 378, 456,
              size=13, secondary=True, center=True)
        button(self.root, "End Workout…", self, "endWorkout:", 26, 480, 150)
        self.next_button = button(self.root, "Next", self, "submit:", 344, 480, 150, primary=True)
        self._show_question()
        self.reveal()
        self.window.makeFirstResponder_(self.answer)
        self._changed()

    @objc.python_method
    def _show_question(self):
        self.expression.setStringValue_(self.session.current_rep.display)
        count, total = self.session.completed, self.session.template.num_of_reps()
        self.progress_label.setStringValue_(f"{count + 1} of {total}")
        self.progress.setDoubleValue_(count)
        self.next_button.setTitle_("Finish" if count + 1 == total else "Next")
        self.answer.setStringValue_("")
        self.show_error("")
        self.window.makeFirstResponder_(self.answer)

    @action
    def submit_(self, sender):
        if self.session is None or self.view_name != "workout":
            return
        answer = self.answer.stringValue().strip().replace("−", "-")
        try:
            int(answer)
        except ValueError:
            self.show_error("Enter a whole number, such as 42 or −7.")
            self.window.makeFirstResponder_(self.answer)
            return
        self.session.submit(answer)
        if not self.session.is_complete:
            self._show_question()
            return
        self.result = self.session.finish()
        self.session = None
        self._save_result()
        self.show_results()
        self._changed()

    @objc.python_method
    def _save_result(self):
        if not self.saved:
            try:
                self.store.record_session(self.result)
                self.saved = True
            except sqlite3.Error:
                traceback.print_exc()

    @action
    def retrySave_(self, sender):
        self._save_result()
        self.show_results()
        self._changed()

    @action
    def quitApplication_(self, sender):
        self.request_quit(lambda: A.NSApplication.sharedApplication().terminate_(None))

    @action
    def quickStart_(self, sender):
        self.start(self.store.last_template())

    @action
    def customWorkout_(self, sender):
        self.show_setup()

    @action
    def history_(self, sender):
        self.show_history()

    @objc.python_method
    def show_results(self):
        self._view("results")
        label(self.root, "Workout complete.", 32, 62, 456, 40, size=30, bold=True)
        label(self.root, template_description(self.result.template), 32, 108, 456, secondary=True)
        card(self.root, 32, 154, 220, 90)
        card(self.root, 268, 154, 220, 90)
        label(self.root, f"{self.result.correct} / {self.result.completed}", 48, 166, 188, 42,
              size=32, bold=True)
        label(self.root, "correct answers", 48, 214, 188, secondary=True)
        label(self.root, duration_text(self.result.duration.total_seconds()), 284, 166, 188, 42,
              size=32, bold=True)
        label(self.root, "time spent", 284, 214, 188, secondary=True)
        mistakes = [(rep, answer) for rep, answer in zip(self.result.workout, self.result.answers)
                    if not matches_answer(rep, answer)]
        if mistakes:
            label(self.root, "A second look", 32, 265, 456, bold=True)
            document = scroll_content(self.root, 298, 165 if self.saved else 120, len(mistakes) * 65)
            for index, (rep, answer) in enumerate(mistakes):
                label(document, f"{rep.display} = {rep.answer()}", 0, index * 65, 428, 28, size=18)
                label(document, f"Your answer: {answer}", 0, index * 65 + 29, 428, size=13, secondary=True)
        else:
            label(self.root, "Every answer correct.", 32, 305, 456, 30, size=18, bold=True)
            label(self.root, "You're all done for now—or ready for another round.",
                  32, 343, 456, 40, secondary=True)
        if self.saved:
            button(self.root, "Do Another", self, "doAnother:", 26, 480, 140)
        else:
            self.show_error("Your results are here, but couldn't be saved. Please retry before closing.")
            button(self.root, "Retry Save", self, "retrySave:", 26, 480, 140)
        button(self.root, "Done", self, "done:", 344, 480, 150, primary=True)
        self.window.makeFirstResponder_(self.root)

    @action
    def doAnother_(self, sender):
        self.start(self.result.template)

    @action
    def done_(self, sender):
        self.window.performClose_(sender)

    @action
    def endWorkout_(self, sender):
        self._confirm_end()

    @objc.python_method
    def _confirm_end(self, after_end=None):
        if self._sheet is not None:
            return
        alert = A.NSAlert.alloc().init()
        alert.setMessageText_("End this workout?")
        alert.setInformativeText_("This unfinished workout won't be saved.")
        alert.addButtonWithTitle_("Keep Going")
        alert.addButtonWithTitle_("End Workout")
        alert.buttons()[1].setHasDestructiveAction_(True)
        self._sheet = alert

        def finished(response):
            self._sheet = None
            if response == A.NSAlertSecondButtonReturn:
                self.session.finish()
                self.session = None
                self.window.orderOut_(None)
                self._changed()
                if after_end is not None:
                    after_end()
            else:
                self.window.makeFirstResponder_(self.answer)

        alert.beginSheetModalForWindow_completionHandler_(self.window, finished)

    def windowShouldClose_(self, sender):
        if self.session is not None:
            self._confirm_end()
            return False
        if self.view_name == "results" and not self.saved:
            self._confirm_discard(lambda: self.window.orderOut_(None))
            return False
        return True

    @objc.python_method
    def _confirm_discard(self, after_discard):
        if self._sheet is not None:
            return
        alert = A.NSAlert.alloc().init()
        alert.setMessageText_("Close without saving?")
        alert.setInformativeText_("This workout couldn't be saved. Keep the results open to retry, or close and discard them.")
        alert.addButtonWithTitle_("Keep Results")
        alert.addButtonWithTitle_("Discard Results")
        alert.buttons()[1].setHasDestructiveAction_(True)
        self._sheet = alert

        def finished(response):
            self._sheet = None
            if response == A.NSAlertSecondButtonReturn:
                self.result = None
                self._changed()
                after_discard()

        alert.beginSheetModalForWindow_completionHandler_(self.window, finished)

    @objc.python_method
    def show_history(self):
        if self.has_pending_work or self._sheet is not None:
            self.reveal()
            return
        self._view("history")
        label(self.root, "Your workouts.", 32, 62, 456, 40, size=30, bold=True)
        totals = self.store.totals()
        workouts_word = "workout" if totals["sessions"] == 1 else "workouts"
        questions_word = "question" if totals["reps"] == 1 else "questions"
        label(self.root, f"{totals['sessions']} {workouts_word} · {totals['reps']} {questions_word} · "
              f"{totals['correct']} correct", 32, 108, 456, secondary=True)
        sessions = self.store.recent_sessions(limit=30)
        if not sessions:
            label(self.root, "A fresh start.", 32, 216, 456, 32, size=22, bold=True, center=True)
            label(self.root, "Your completed workouts will appear here.", 32, 258, 456,
                  secondary=True, center=True)
        else:
            label(self.root, "Recent sessions", 32, 159, 456, bold=True)
            document = scroll_content(self.root, 196, 224, len(sessions) * 78)
            for index, session in enumerate(sessions):
                try:
                    timestamp = datetime.fromisoformat(session.finished_at).strftime("%d %b · %H:%M")
                    description = template_description(WorkoutTemplate.parse(session.template))
                except ValueError:
                    timestamp, description = session.finished_at, session.template
                label(document, timestamp, 0, index * 78, 220, size=15, bold=True)
                score = label(document, f"{session.correct}/{session.completed_reps} · "
                              f"{duration_text(session.duration_sec)}", 240, index * 78, 188, size=15)
                score.setAlignment_(A.NSTextAlignmentRight)
                label(document, description, 0, index * 78 + 28, 428, size=13, secondary=True)
            if totals["sessions"] > len(sessions):
                label(self.root, "Showing your latest 30 workouts.", 32, 434, 456, size=12, secondary=True)
        button(self.root, "Clear History…", self, "clearHistory:", 26, 480, 150)
        button(self.root, "Done", self, "done:", 344, 480, 150, primary=True)
        self.reveal()

    @action
    def clearHistory_(self, sender):
        if self._sheet is not None or not self.store.totals()["sessions"]:
            return
        alert = A.NSAlert.alloc().init()
        alert.setMessageText_("Clear workout history?")
        alert.setInformativeText_("This permanently deletes all saved workouts. Your workout settings will be kept.")
        alert.addButtonWithTitle_("Keep History")
        alert.addButtonWithTitle_("Clear History")
        alert.buttons()[1].setHasDestructiveAction_(True)
        self._sheet = alert

        def finished(response):
            self._sheet = None
            if response == A.NSAlertSecondButtonReturn:
                try:
                    self.store.clear_history()
                    self.show_history()
                except Exception as exc:
                    traceback.print_exc()
                    self.show_error(f"Couldn't clear history: {exc}")

        alert.beginSheetModalForWindow_completionHandler_(self.window, finished)
