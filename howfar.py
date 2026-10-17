#!/usr/bin/env python3
"""howfar: a progress bar that AI coding agents update themselves.

The percent is the agent's own estimate from weighted milestones, not a measurement.
State lives in ./progress.json (override with HOWFAR_FILE).
"""
import json
import os
import sys
import time

USAGE = """usage: howfar.py <command> [args]
  plan "Task" "Step:weight" ...   start a task with weighted milestones
  start "Step"                    set the current step
  done "Step"                     mark a milestone finished
  set 68 ["text"]                 manual percent override
  show                            full view
  line                            one short line for status bars
  watch                           redraw the full view every second
  --version                       print the version"""

__version__ = "0.1.0"
BAR_WIDTH = 20


class Error(Exception):
    pass


def state_path():
    return os.environ.get("HOWFAR_FILE", "progress.json")


def load():
    try:
        with open(state_path(), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise Error('no plan yet. Start one with: howfar.py plan "Task" "Step:weight" ...')


def save(state):
    path = state_path()
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, path)


def percent(state):
    if state.get("override") is not None:
        return state["override"]
    total = sum(s["weight"] for s in state["steps"])
    done = sum(s["weight"] for s in state["steps"] if s["done"])
    return round(done * 100 / total)


def fmt_duration(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60:02d}s"
    return f"{seconds // 3600}h {seconds % 3600 // 60:02d}m"


def eta(elapsed, pct):
    if pct <= 0:
        return "estimating..."
    if pct >= 100:
        return "done"
    return "~" + fmt_duration(elapsed * (100 - pct) / pct) + " left"


def find_step(state, name):
    key = name.casefold()
    for s in state["steps"]:
        if s["name"].casefold() == key:
            return s
    matches = [s for s in state["steps"] if s["name"].casefold().startswith(key)]
    if len(matches) == 1:
        return matches[0]
    names = ", ".join(s["name"] for s in state["steps"])
    if matches:
        raise Error(f'step "{name}" is ambiguous. Steps: {names}')
    raise Error(f'unknown step "{name}". Steps: {names}')


def bar(pct):
    filled = round(BAR_WIDTH * pct / 100)
    return "[" + "#" * filled + "-" * (BAR_WIDTH - filled) + "]"


def render_line(state):
    pct = percent(state)
    return f"{bar(pct)} {pct:3d}% | {state['current']} | {eta(time.time() - state['started'], pct)}"


def render_full(state):
    pct = percent(state)
    lines = [
        state["task"],
        f"{bar(pct)} {pct}%",
        f"ETA: {eta(time.time() - state['started'], pct)}   elapsed {fmt_duration(time.time() - state['started'])}",
        f"Current: {state['current']}",
        "",
    ]
    for s in state["steps"]:
        mark = "✓" if s["done"] else ("→" if s["name"] == state["current"] else "○")
        lines.append(f"  {mark} {s['name']} ({s['weight']})")
    return "\n".join(lines)


def cmd_plan(args):
    if len(args) < 2:
        raise Error('plan needs a task and at least one "Step:weight"')
    steps = []
    for spec in args[1:]:
        name, sep, weight = spec.rpartition(":")
        if not sep or not name or not weight.strip().isdigit():
            raise Error(f'bad milestone "{spec}", expected "Step:weight" with an integer weight')
        steps.append({"name": name.strip(), "weight": int(weight), "done": False})
    if sum(s["weight"] for s in steps) <= 0:
        raise Error("total weight must be above 0")
    return {"task": args[0], "steps": steps, "current": steps[0]["name"],
            "started": time.time(), "override": None}


def cmd_start(state, args):
    if len(args) != 1:
        raise Error('start needs one step name')
    state["current"] = find_step(state, args[0])["name"]


def cmd_done(state, args):
    if len(args) != 1:
        raise Error('done needs one step name')
    find_step(state, args[0])["done"] = True
    state["override"] = None
    pending = [s["name"] for s in state["steps"] if not s["done"]]
    state["current"] = pending[0] if pending else "Finished"


def cmd_set(state, args):
    if not args or len(args) > 2:
        raise Error('set needs a percent and optional text, e.g. set 68 "Writing tests"')
    try:
        pct = round(float(args[0]))
    except ValueError:
        raise Error(f'set needs a number, got "{args[0]}"')
    state["override"] = max(0, min(100, pct))
    if len(args) == 2:
        state["current"] = args[1]


def watch():
    try:
        while True:
            try:
                view = render_full(load())
            except Error as e:
                view = f"howfar: {e}"
            print("\033[2J\033[H" + view, flush=True)
            time.sleep(1)
    except KeyboardInterrupt:
        pass


def main(argv):
    if not argv:
        raise Error(USAGE)
    cmd, args = argv[0], argv[1:]
    if cmd == "plan":
        state = cmd_plan(args)
    elif cmd in ("start", "done", "set"):
        state = load()
        {"start": cmd_start, "done": cmd_done, "set": cmd_set}[cmd](state, args)
    elif cmd == "show":
        print(render_full(load()))
        return
    elif cmd == "line":
        print(render_line(load()))
        return
    elif cmd == "watch":
        watch()
        return
    elif cmd == "--version":
        print(f"howfar {__version__}")
        return
    else:
        raise Error(f'unknown command "{cmd}"\n{USAGE}')
    save(state)
    print(render_line(state))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    try:
        main(sys.argv[1:])
    except Error as e:
        print(f"howfar: {e}", file=sys.stderr)
        sys.exit(1)
