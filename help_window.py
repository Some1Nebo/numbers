"""A reusable, non-modal Help window that leaves an active workout intact."""

import AppKit as A
import objc

from native_ui import branded_content, button, create_window, label, reveal_window


class HelpWindow(A.NSObject):
    def init(self):
        self = objc.super(HelpWindow, self).init()
        if self is None:
            return None
        self.window = create_window("Numbers Help")
        root = branded_content()
        self.window.setContentView_(root)
        label(root, "How it works.", 32, 62, 456, 40, size=30, bold=True)
        label(root, "A little mental gymnastics.", 32, 108, 456, secondary=True)
        sections = (
            ("Make it yours", "Start Workout repeats your last settings. Use Custom Workout "
             "to choose difficulty, operations and length."),
            ("Take your time", "Type a whole-number answer and press Return. Your score, "
             "corrections and elapsed time appear at the end."),
            ("Your workout history", "Completed workouts are saved on this Mac. Find them "
             "in History. Unfinished workouts aren't saved."),
        )
        for index, (title, text) in enumerate(sections):
            top = 162 + index * 100
            label(root, title, 32, top, 456, size=16, bold=True)
            label(root, text, 32, top + 31, 456, 60, secondary=True)
        button(root, "Done", self, "done:", 344, 480, 150, primary=True)
        return self

    @objc.python_method
    def reveal(self):
        reveal_window(self.window)

    def done_(self, sender):
        self.window.performClose_(sender)
