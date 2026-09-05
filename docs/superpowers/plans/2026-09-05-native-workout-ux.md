# Native workout UX implementation plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task by task. Keep the work in this session.

**Goal:** Make Numbers a calm, keyboard-friendly mental break, with quick start, visual setup, one persistent workout window, and results only at the end.

**Architecture:** A framework-independent `WorkoutSession` owns progression and results. The console adapter remains synchronous; the native window advances the same session from AppKit actions. Small AppKit view helpers handle visual styling; the menu-bar application owns storage, preferences, and window lifetime.

**Tech Stack:** Existing Python, unittest, rumps, PyObjC/AppKit, SQLite, PyInstaller. No new dependencies.

**Spec:** Agreed design in the current task: setup → workout → results, remembered configuration, no correctness feedback or running timer during a workout, corrected mistakes at the end, native styling and existing dumbbell icon. Percentages/fractions are a later change.

## Global constraints

- Preserve the console front-end, existing database history, and arithmetic difficulty.
- Keep correctness feedback at the end only. Reject malformed input without judging mathematical correctness.
- Show elapsed time only in results.
- Keep the menu bar icon unchanged.
- Use isolated temporary databases for verification; do not save synthetic sessions to personal history.

## Tasks

- [x] **1. Session model and structured arithmetic.** Extend `test/test_rep.py` to reject executable expressions, preserve console formatting, render native operators and ensure generated division answers are integers. Add progression/abort/finalisation tests in `test/test_runner.py`. Refactor `Rep` to structured operands and `WorkoutSession(template, workout=None)` with `current_rep`, `submit(answer)`, `is_complete`, `finish()`. Keep `run_workout(template, ask_answer)` as the console adapter. Run `.venv/bin/python -m unittest discover -s test -v`.
- [x] **2. Remembered setup.** Extend `SessionStore` with a small additive preferences table and methods `last_template()` and `remember_template(template)`. Test reopening, invalid saved values, and old-schema migration in `test/test_storage.py`. Keep the existing default `m-*-10` when no valid preference exists. No session-data migration.
- [x] **3. Native views and integration.** Add `native_ui.py` for native control construction and `workout_window.py` for setup/workout/results. Setup offers difficulty, four operation toggles, and editable rep count. Show a stable large expression, answer field, progress, Next/Finish, and End Workout; no correctness until results. Results show accuracy, elapsed time, scrollable corrections and Do Another/Done. Window close during a workout confirms ending; Cancel keeps answers and focus. Replace modal session flow in `menubar.py`, add Quick Start and Custom Workout, move history clearing under history. Use AppKit smoke tests with temporary storage for completed/aborted sessions, invalid answers, close behaviour, persistence and repeat.
- [x] **4. Review and verify.** Run all tests, build the app, inspect and exercise the actual native UI through Computer Use in an isolated data directory. Check light/dark rendering, keyboard entry, invalid setup, end/cancel, long results, repeat, and menu return. Update README with the new UX and module layout. Leave a runnable build and report verification plus any limitations.

## Review notes

The synchronous callback remains for console compatibility; the UI does not start nested modal loops per question. Structured operands remove `eval` and allow display symbols without reparsing strings. Preferences are separate from history so clearing sessions does not reset the user's workout. No adaptive difficulty, streaks, per-question timing, new exercise types, or dependency migration in this pass.

## Verification — 2026-09-05

- `NUMBERS_UI_TESTS=1 .venv/bin/python -W error::ResourceWarning -m unittest discover -s test -v`: 42 passed, no warnings.
- Console subprocess smoke check: completed and saved one workout in a temporary directory.
- PyInstaller build completed successfully for arm64.
- Independent code review found a stale-menu state after save retry; fixed with an integration regression test.
- Live Computer Use checks: light/dark screens, actual Return submission, invalid input, Cmd-A, paste, Undo/Redo, Cmd-N, Cmd-W, Keep Going, end without saving, mixed/perfect results, history, and scrolling to the last of 20 mistakes.
- Help uses a separate non-modal window with the shared dumbbell/NUMBERS header. Reopening Help preserves an active workout and its typed answer; covered by an integration test and visual inspection.
- Development previews used temporary data before installation; no synthetic workouts were added to personal history.
