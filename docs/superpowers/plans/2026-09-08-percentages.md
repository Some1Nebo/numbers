# Percentage Workouts Implementation Plan

**Goal:** Add selectable percentage exercises, alone or mixed, with manageable numbers.
**Architecture:** A separate PercentageRep implements the same display/answer interface as Rep. Each exercise owns parsing and answer matching; the session stays independent of exercise type. Decimal answers are saved as canonical strings (SQLite numeric affinity remains backward compatible); historical rows are untouched.
**Tech Stack:** Python standard library Decimal, SQLite, AppKit.
**Spec:** Approved conversation: percentage-of, increase/decrease, percentage ratio; reverse percentages on Hard. Whole answers on Simple, tidy decimals on Medium, explicit two-place half-up rounding on Hard. No in-session correctness or timer. Preserve legacy wildcard meaning; p explicitly opts into percentages.

## Tasks
- [x] Add tests for formulas, rounding boundaries, invalid input, difficulty constraints and p/mixed template parsing. Run them before implementation.
- [x] Implement percentage_rep.py with prompt, instruction, answer, parse_answer and matches_answer; add equivalent integer methods to Rep and delegate runner checking. Generate Simple from familiar rates and multiples of 100, Medium from friendly rates and multiples of 20, Hard with reverse questions and smaller varied operands.
- [x] Test decimal persistence and mixed sessions; store canonical decimal text without changing historical rows or schema.
- [x] Add fifth operation button, readable multiline prompts, instruction text, decimal validation and formatted corrections. Update Help and README, preserve console behavior.
- [x] Run all tests including AppKit; inspect percentage UI and review diff; build app. Keep deployment separate until requested.

Validation command: NUMBERS_UI_TESTS=1 .venv/bin/python -W error::ResourceWarning -m unittest discover -s test -v

## Verification

52 tests passed including 9 native AppKit checks. Visually checked percentage setup, long reverse prompts, rounding instructions, silent progression and scrollable corrections in dark appearance; long prompts also checked in light appearance. PyInstaller 2.2 build and signature verification succeeded. Personal database was not used for previews.
