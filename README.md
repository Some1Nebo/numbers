# Numbers Workout

A little mental gymnastics: short sessions of random arithmetic questions
(addition, subtraction, multiplication, division) in three difficulty modes.

Two front-ends share the same core (`runner.py`) and save completed workouts
to a local SQLite database:

| Front-end | How to run |
|---|---|
| **Menu bar app** (tray icon, no Dock entry) | `~/Applications/Numbers Workout.app` (auto-starts at login), or `.venv/bin/python menubar.py` |
| **Console** | `.venv/bin/python console_app.py` |

## Using the Mac app

- **Start Workout** starts immediately with your last settings (initially medium,
  all operations, 10 questions). During a workout this becomes **Return to Workout**.
- **Custom Workout…** opens native difficulty and operation controls and an editable
  question count (1–1,000). Your choices are remembered when you start.
- One window stays in place for the whole workout. Type an integer and press
  **Return** or click **Next**. Negative answers are supported. Standard Mac
  selection, copy, paste, and undo shortcuts work in text fields.
- There is no correctness feedback or running timer during the workout. Results
  show your score, elapsed time, and mistakes with your answer and the correct answer.
- **Do Another** starts a fresh workout with the same settings. **Done** closes the
  window; the app stays in the menu bar.
- **Help** opens a matching native window without interrupting an active workout.
- **History…** shows all-time counts and the latest 30 sessions. **Clear History…**
  lives inside that window and requires confirmation; workout settings are retained.
- Ending an unfinished workout requires confirmation and does not save it.
  A failed save keeps completed results available for retry.

The window follows macOS light/dark appearance. It comes forward when opened and
lets you switch freely to other apps. With a window active, **⌘N** starts your usual
workout, **⇧⌘N** opens custom setup, and **⌘W** closes the window (or asks to end a
workout). New-workout actions return to an already active workout.

To launch directly into setup from source:

```bash
.venv/bin/python menubar.py --setup
```

## Console workout template syntax

`{mode}-{rep_types}-{num_of_reps}`, e.g. `m-*-10`:

- mode: `s` simple, `m` medium, `h` hard
- rep_types: `a` addition, `s` subtraction, `m` multiplication, `d` division, `*` all
  (comma-separated, e.g. `a,m`)
- num_of_reps: integer

Default: `m-*-10`.

## Storage

SQLite at `~/Library/Application Support/numbers-workout/numbers.db`
(override the directory with the `NUMBERS_WORKOUT_HOME` env var).

- `sessions` — one row per session: timestamps, duration, template, correct/wrong counts, score
- `session_reps` — one row per rep: the expression, your answer, the correct answer, was it correct
- `preferences` — remembered Mac workout settings, separate from session history

Existing databases are upgraded additively, without rewriting sessions or answers.
Each workout and its answers are saved in one transaction. Timing uses a monotonic
clock for duration and wall-clock timestamps for history. Per-question timing is
not recorded.

## Setup (fresh machine)

```bash
/opt/homebrew/bin/python3.14 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Icons

```bash
.venv/bin/python make_icons.py   # regenerates menubar_icon.png, app_icon_1024.png, app_icon.icns
```

The menu bar icon prefers an SF Symbol (`dumbbell`) at runtime and only falls
back to the bundled `menubar_icon.png` if symbols are unavailable.

## Build the .app bundle

```bash
.venv/bin/pyinstaller --noconfirm --clean menubar.spec
```

Produces `dist/Numbers Workout.app` (native arm64). The spec adds the macOS
`BUNDLE` target; `LSUIElement=true` in `info.plist.json` makes it a
menu-bar-only app (no Dock icon).

## Install + auto-start at login

```bash
./install_autostart.sh
```

Copies the bundle to `~/Applications/` and installs a LaunchAgent
(`~/Library/LaunchAgents/com.sergey.numbers-workout.plist`, `RunAtLoad`) so the
icon appears in the menu bar at every login. Logs go to
`~/Library/Logs/numbers-workout.{out,err}.log`.

To remove autostart:

```bash
launchctl bootout gui/$(id -u)/com.sergey.numbers-workout
rm ~/Library/LaunchAgents/com.sergey.numbers-workout.plist
```

## Tests

```bash
.venv/bin/python -m unittest discover -s test -v
```

The AppKit integration checks are opt-in because they open real windows and require
a logged-in Mac graphical session. All their data goes to temporary databases:

```bash
NUMBERS_UI_TESTS=1 .venv/bin/python -m unittest discover -s test -v
```

For manual visual checks with disposable data (no personal history or system
appearance changes):

```bash
.venv/bin/python test/preview_ui.py --appearance light --scene results
.venv/bin/python test/preview_ui.py --appearance dark --scene setup
```

Scenes: `setup`, `workout`, `results`, `history`, `help`. Results include 20 deliberately
incorrect answers for checking the scrollable review.

## Layout

- `rep.py` — structured integer arithmetic and generation per mode/type; no `eval`
- `workout_template.py` — template parsing
- `workout.py` — workout (list of reps) generation
- `runner.py` — event-driven `WorkoutSession`, `SessionResult`, and synchronous console adapter
- `storage.py` — SQLite `SessionStore`
- `console_app.py` — console front-end (was `numbers.py`; renamed because
  `numbers.py` shadowed the stdlib `numbers` module and broke third-party
  imports like Pillow)
- `menubar.py` — menu bar, app lifetime and service ownership (rumps)
- `workout_window.py` — native setup, workout, results, history and confirmation flows
- `help_window.py` — independent Help window using the same header and styling
- `native_ui.py` — native controls, layout helpers, presentation formatting and editing menu
- `menubar.spec`, `make_icons.py`, `info.plist.json`, `install_autostart.sh` — packaging
