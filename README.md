# Numbers Workout

Mental-arithmetic trainer: short sessions of random arithmetic reps (addition,
subtraction, multiplication, division) in three difficulty modes.

Two front-ends share the same core (`runner.py`) and both save every session
to a local SQLite database:

| Front-end | How to run |
|---|---|
| **Menu bar app** (tray icon, no Dock entry) | `~/Applications/Numbers Workout.app` (auto-starts at login), or `.venv/bin/python menubar.py` |
| **Console** | `.venv/bin/python console_app.py` |

## Workout template syntax

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

An analytics layer can be built directly on top of these two tables.
The menu bar app shows *Recent Sessions* and *All-time Stats* from them.

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

## Layout

- `rep.py` — rep (expression) generation per mode/type
- `workout_template.py` — template parsing
- `workout.py` — workout (list of reps) generation
- `runner.py` — shared session loop + `SessionResult`
- `storage.py` — SQLite `SessionStore`
- `console_app.py` — console front-end (was `numbers.py`; renamed because
  `numbers.py` shadowed the stdlib `numbers` module and broke third-party
  imports like Pillow)
- `menubar.py` — menu bar front-end (rumps)
- `menubar.spec`, `make_icons.py`, `info.plist.json`, `install_autostart.sh` — packaging
