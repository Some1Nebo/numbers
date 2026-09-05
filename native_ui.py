"""Small AppKit construction helpers shared by the workout's native views.

Frames use points measured from the top. The window has a fixed content size;
long collections scroll instead of changing the position of the answer field.
System colours follow the user's light/dark appearance automatically.
"""

import AppKit as A

WIDTH, HEIGHT = 520, 540


def create_window(title):
    style = A.NSWindowStyleMaskTitled | A.NSWindowStyleMaskClosable | A.NSWindowStyleMaskMiniaturizable
    window = A.NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
        A.NSMakeRect(0, 0, WIDTH, HEIGHT), style, A.NSBackingStoreBuffered, False)
    window.setTitle_(title)
    window.setTitleVisibility_(A.NSWindowTitleHidden)
    window.setTitlebarAppearsTransparent_(True)
    window.setReleasedWhenClosed_(False)
    window.setCollectionBehavior_(A.NSWindowCollectionBehaviorMoveToActiveSpace)
    window.center()
    return window


def reveal_window(window):
    # Menu-bar-only apps need explicit activation, but a normal window lets
    # the user switch freely to other apps instead of floating above them.
    A.NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
    window.deminiaturize_(None)
    window.makeKeyAndOrderFront_(None)


def branded_content():
    root = A.NSView.alloc().initWithFrame_(A.NSMakeRect(0, 0, WIDTH, HEIGHT))
    symbol = A.NSImage.imageWithSystemSymbolName_accessibilityDescription_("dumbbell", "Numbers Workout")
    if symbol is not None:
        icon = A.NSImageView.alloc().initWithFrame_(frame(root, 32, 20, 24, 24))
        icon.setImage_(symbol)
        icon.setContentTintColor_(A.NSColor.secondaryLabelColor())
        root.addSubview_(icon)
    label(root, "NUMBERS", 66, 23, 200, size=12, bold=True, secondary=True)
    return root


class FlippedView(A.NSView):
    def isFlipped(self):
        return True


def frame(parent, x, top, width, height):
    y = top if parent.isFlipped() else parent.bounds().size.height - top - height
    return A.NSMakeRect(x, y, width, height)


def label(parent, text, x, top, width, height=24, size=14, bold=False,
          secondary=False, center=False):
    field = A.NSTextField.labelWithString_(text)
    field.setFrame_(frame(parent, x, top, width, height))
    field.setFont_(A.NSFont.systemFontOfSize_weight_(
        size, A.NSFontWeightSemibold if bold else A.NSFontWeightRegular))
    field.setTextColor_(A.NSColor.secondaryLabelColor() if secondary else A.NSColor.labelColor())
    field.setAlignment_(A.NSTextAlignmentCenter if center else A.NSTextAlignmentLeft)
    field.setLineBreakMode_(A.NSLineBreakByWordWrapping)
    field.setMaximumNumberOfLines_(0)
    parent.addSubview_(field)
    return field


def button(parent, title, target, action, x, top, width, height=36, primary=False):
    control = A.NSButton.buttonWithTitle_target_action_(title, target, action)
    control.setFrame_(frame(parent, x, top, width, height))
    control.setBezelStyle_(A.NSBezelStyleRounded)
    control.setControlSize_(A.NSControlSizeLarge)
    control.setFont_(A.NSFont.systemFontOfSize_(14))
    if primary:
        control.setKeyEquivalent_("\r")
    parent.addSubview_(control)
    return control


def card(parent, x, top, width, height):
    box = A.NSBox.alloc().initWithFrame_(frame(parent, x, top, width, height))
    box.setBoxType_(A.NSBoxCustom)
    box.setTitlePosition_(A.NSNoTitle)
    box.setBorderType_(A.NSNoBorder)
    box.setTransparent_(False)
    box.setFillColor_(A.NSColor.quaternaryLabelColor())
    box.setCornerRadius_(14)
    parent.addSubview_(box)
    return box


def install_application_menu(target):
    """Provide normal responder-chain shortcuts in this menu-bar-only app.

    rumps builds a status-item menu, not an application menu. Without the latter
    AppKit has no Cmd-A/C/V/X equivalents to route to the active field editor.
    """
    menu = A.NSMenu.alloc().initWithTitle_("Numbers Workout")
    groups = (
        ("Numbers Workout", (("Quit Numbers", "quitApplication:", "q", target),)),
        ("File", (("Start Workout", "quickStart:", "n", target),
                  ("Custom Workout…", "customWorkout:", "N", target),
                  ("History…", "history:", "", target),
                  ("Close Window", "performClose:", "w", None))),
        ("Edit", (("Undo", "undo:", "z", None), ("Redo", "redo:", "Z", None),
                  ("Cut", "cut:", "x", None), ("Copy", "copy:", "c", None),
                  ("Paste", "paste:", "v", None), ("Select All", "selectAll:", "a", None))),
    )
    for title, items in groups:
        parent = A.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, "")
        submenu = A.NSMenu.alloc().initWithTitle_(title)
        for name, action, key, receiver in items:
            item = A.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(name, action, key)
            item.setTarget_(receiver)
            if key in ("Z", "N"):
                item.setKeyEquivalentModifierMask_(A.NSEventModifierFlagCommand | A.NSEventModifierFlagShift)
            submenu.addItem_(item)
        parent.setSubmenu_(submenu)
        menu.addItem_(parent)
    A.NSApplication.sharedApplication().setMainMenu_(menu)


def scroll_content(parent, top, height, content_height):
    scroll = A.NSScrollView.alloc().initWithFrame_(frame(parent, 32, top, 456, height))
    scroll.setDrawsBackground_(False)
    scroll.setHasVerticalScroller_(True)
    scroll.setAutohidesScrollers_(True)
    document = FlippedView.alloc().initWithFrame_(A.NSMakeRect(0, 0, 436, max(height, content_height)))
    scroll.setDocumentView_(document)
    parent.addSubview_(scroll)
    return document


def duration_text(seconds):
    seconds = round(seconds)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes}m {seconds:02d}s" if minutes else f"{seconds}s"


MODES = (("s", "Simple"), ("m", "Medium"), ("h", "Hard"))
OPERATIONS = (("a", "+", "Addition"), ("s", "−", "Subtraction"),
              ("m", "×", "Multiplication"), ("d", "÷", "Division"))


def template_description(template):
    mode = dict(MODES)[template.mode()]
    operations = "Mixed" if len(template.rep_types()) == 4 else " ".join(
        symbol for key, symbol, _ in OPERATIONS if key in template.rep_types())
    count = template.num_of_reps()
    return f"{mode} · {operations} · {count} {'question' if count == 1 else 'questions'}"
