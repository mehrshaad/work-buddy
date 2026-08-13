#!/usr/bin/env python3
"""Work Buddy — SwiftBar menu bar plugin.

<xbar.title>Work Buddy</xbar.title>
<xbar.author>Ali</xbar.author>
<xbar.desc>Pause and resume workday tracking, and see the day at a glance.</xbar.desc>
<xbar.dependencies>python3</xbar.dependencies>

Renders entirely from `worklog status`, `worklog apps` and `worklog config`, so the
plugin holds no logic of its own — anything it shows is something the CLI already
knows, and every click is a command you could type yourself.
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
WORKLOG = next((p for p in (HOME / ".local/bin/worklog",
                            HOME / ".worklog/bin/worklog.py") if p.exists()),
               HOME / ".local/bin/worklog")
PY = "/opt/homebrew/bin/python3"
ASSETS = HOME / ".worklog" / "assets"
FONT = "size=13"


def run(*args, timeout=25):
    cmd = ([str(WORKLOG)] if WORKLOG.suffix != ".py" else [PY, str(WORKLOG)]) + list(args)
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                             env={**os.environ,
                                  "PATH": "/opt/homebrew/bin:/usr/bin:/bin:" + os.environ.get("PATH", "")})
        return out.stdout.strip(), out.returncode
    except Exception:
        return "", 1


def jrun(*args):
    out, rc = run(*args)
    if rc != 0 or not out:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None


def img(name):
    p = ASSETS / name
    if not p.is_file():
        return ""
    return " | templateImage=" + base64.b64encode(p.read_bytes()).decode()


def act(label, *args, extra=""):
    """A clickable item that runs the CLI and refreshes the menu."""
    params = " ".join(f"param{i + 1}={a}" for i, a in enumerate(args))
    binary = str(WORKLOG) if WORKLOG.suffix != ".py" else PY
    if WORKLOG.suffix == ".py":
        params = f"param1={WORKLOG} " + " ".join(
            f"param{i + 2}={a}" for i, a in enumerate(args))
    print(f"{label} | bash={binary} {params} terminal=false refresh=true {FONT}{extra}")


st = jrun("status")
if st is None:
    print("⚠" + img("menubar-paused@2x.png"))
    print("---")
    print(f"Work Buddy could not reach the CLI | color=#c0392b {FONT}")
    print(f"Checked: {WORKLOG} | {FONT}")
    sys.exit(0)

# ---------------------------------------------------------------- menu bar ----
paused = st.get("paused")
if paused:
    left = st.get("minutes_left")
    label = "∞" if st.get("indefinite") or left is None else f"{left}m"
    print(f" {label}" + img("menubar-paused@2x.png"))
else:
    print(f" {st.get('active_today', '')}".rstrip() + img("menubar-tracking@2x.png"))

print("---")

# ------------------------------------------------------------------ status ----
print(f"Work Buddy | {FONT} md=true")
state = st.get("state", "")
colour = "#e67e22" if paused else "#27ae60"
print(f"{'Paused' if paused else 'Tracking'} — {state} | color={colour} {FONT}")
if not st.get("work_time"):
    print(f"Outside work hours — the sampler is idle anyway | color=#7f8c8d {FONT}")
if st.get("paused_today_minutes"):
    print(f"Paused {st['paused_today_minutes']:g}m today | color=#7f8c8d {FONT}")

print("---")
if paused:
    act("▶︎  Resume tracking", "resume")
else:
    for mins, text in ((15, "15 minutes"), (30, "30 minutes"), (60, "1 hour")):
        act(f"⏸  Pause {text}", "pause", "--minutes", str(mins))
    act("⏸  Pause until end of day", "pause", "--until", "17:00")
    act("⏸  Pause until I resume", "pause", "--indefinite")

# -------------------------------------------------------------------- today ----
print("---")
print(f"Today | {FONT}")
print(f"--Active: {st.get('active_today', '0m')} | {FONT}")
print(f"--Meetings: {st.get('meetings_today', 0)} | {FONT}")
if st.get("current_meeting"):
    print(f"In a meeting: {st['current_meeting']} | color=#2980b9 {FONT}")
degraded = st.get("degraded_days") or []
if degraded:
    print(f"⚠ {len(degraded)} day(s) awaiting summary | color=#e67e22 {FONT}")
    for d in degraded:
        print(f"--{d} | {FONT}")
    act("--Summarize them now", "repair")

# --------------------------------------------------------------------- apps ----
print("---")
print(f"Apps | {FONT}")
apps = jrun("apps", "--days", "7") or []
if not apps:
    print(f"--Nothing sampled yet | color=#7f8c8d {FONT}")
for a in apps[:22]:
    mark = "☒" if a["excluded"] else "☑"
    verb = "include-app" if a["excluded"] else "exclude-app"
    mins = f"  ({a['minutes']}m)" if a.get("minutes") else ""
    act(f"--{mark}  {a['app']}{mins}", "config", verb, a["app"].replace(" ", "\\ "))
print(f"--- | {FONT}")
print(f"--Ticked apps are recorded; unticked are ignored entirely | color=#7f8c8d {FONT}")

# ----------------------------------------------------------------- settings ----
print(f"Settings | {FONT}")
cfg = jrun("config", "get") or {}
wh = cfg.get("work_hours", {})
print(f"--Work hours: {wh.get('start', '?')} – {wh.get('end', '?')} | {FONT}")
for end in ("16:00", "17:00", "18:00", "19:00"):
    act(f"----End at {end}", "config", "set", "work_hours.end", end)
print(f"--Pause reminder: every {(cfg.get('pause') or {}).get('reminder_minutes', 30)}m | {FONT}")
for n in (15, 30, 60, 0):
    act(f"----{'Never' if n == 0 else f'Every {n}m'}", "config", "set",
        "pause.reminder_minutes", str(n))
print(f"--Sources | {FONT}")
for key, name in (("git", "Git commits"), ("shell", "Shell history"),
                  ("calendar", "Calendar feed"), ("cloud", "OneDrive files"),
                  ("claude_code", "Claude Code"), ("mis_board", "Tracker export")):
    on = bool((cfg.get(key) or {}).get("enabled"))
    act(f"----{'☑' if on else '☐'}  {name}", "config", "set", f"{key}.enabled",
        "false" if on else "true")

# ---------------------------------------------------------------- shortcuts ----
print("---")
act("Write today's report now", "report")
today = st.get("today", "")
outdir = cfg.get("output_dir") or "~/Documents/Work Log"
log = Path(os.path.expanduser(outdir)) / f"{today}.md"
if log.is_file():
    print(f"Open today's log | bash=/usr/bin/open param1={log} terminal=false {FONT}")
print(f"Open the log folder | bash=/usr/bin/open param1={log.parent} terminal=false {FONT}")
print(f"Refresh | refresh=true {FONT}")
