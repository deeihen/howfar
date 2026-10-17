## Progress reporting (aiprogress)

Report your progress on every multi-step task with `aiprogress.py`:

1. Before any work, run `python3 aiprogress.py plan "<task>" "<Milestone>:<weight>" ...` with 4 to 8 milestones whose weights add up to 100. Weight each milestone by expected effort.
2. Run `python3 aiprogress.py start "<Milestone>"` before you begin a milestone.
3. Run `python3 aiprogress.py done "<Milestone>"` after it is finished. Only mark a milestone done when it actually works (code runs, tests pass), not when you have merely written it.
4. If the scope changes, run `plan` again with the new milestones instead of bending the old ones.
5. Use `python3 aiprogress.py set <percent> "<text>"` only for a rough manual correction; the next `done` clears it.
