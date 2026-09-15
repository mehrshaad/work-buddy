<p align="center">
  <img src="assets/icon-256.png" width="112" alt="Work Buddy">
</p>

<h1 align="center">Work Buddy</h1>

<p align="center">
  A quiet macOS companion that writes your workday log for you — and stops watching the moment you ask.
</p>

---

Work Buddy samples what you are working on during your work hours, gathers the evidence
your machine already holds — commits, Claude Code sessions, calendar meetings, files you
touched — and at the end of the day turns it into a markdown work log plus a table of
tracker rows you can paste straight into your team's board.

It lives in the menu bar. Its eyes are open while it is recording and closed while it is
paused.

<p align="center">
  <img src="assets/menubar-tracking@2x.png" width="26" alt="tracking">
  &nbsp;&nbsp;recording&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/menubar-paused@2x.png" width="26" alt="paused">
  &nbsp;&nbsp;paused
</p>

## What it records

| Source | How |
| --- | --- |
| Foreground app and window titles | one sample a minute, inside your work hours only |
| Meetings you joined | a meeting window being *open* counts, so a call you work through is credited in full |
| Meetings you were booked for | a published calendar `.ics` feed or a saved export |
| Git commits | every repo under your scan roots, filtered to your own author emails |
| Claude Code sessions | title, branch, files changed, what each command was for, where you left off |
| Claude Code token usage | turns, cache-read, context size and sessions carrying hundreds of turns of old context — read from the ledger [tokenwise](https://github.com/kushalsamani/tokenwise) keeps, if it is installed |
| Files touched | your cloud-sync folders |
| Shell history | timestamped entries only |
| Tracker export | tasks you logged yourself, read from a spreadsheet export |

Nothing leaves your machine except the summarization call to the Claude CLI.

## Pausing

Personal time should not be in a work log, so pausing is a first-class feature rather
than an afterthought.

```
worklog pause --minutes 30     # or --until 14:00, or --indefinite
worklog resume
```

While paused, no sample is written at all, and **every other source is filtered too** —
commits, sessions, meetings, files and shell history whose timestamps fall inside the
pause are left out of the report. Paused time counts as neither active nor idle, so the
day's totals simply come out lower.

Two deliberate choices worth knowing:

- **Containment, not overlap.** An item is dropped only if it sits *entirely* inside a
  pause. A three-hour session is not lost because you paused for fifteen minutes in the
  middle of it.
- **A pause is editable, so it is reversible.** Windows are appended to
  `pauses.jsonl`. Collectors read that file and a repair re-collects from source, so if
  you forget to resume over a real working afternoon, trim the line and run
  `worklog repair --date <day>` — the work comes back. Nothing is destroyed.

An indefinite pause still expires at the end of your workday, and reminds you every half
hour while it is open, because the expensive failure is forgetting it is on.

## Self-repair

The report runs at the end of the day, which is exactly when a laptop tends to be shut or
offline. If the summarizer cannot reach the Claude CLI it writes the raw evidence instead
and marks the day as degraded; a second agent retries every weekday morning. Days missed
entirely are also detected and filled in.

```
worklog repair --dry-run     # what is degraded and why
worklog repair               # fix it
```

## Monthly timesheet

One workbook, one sheet per month, written when the month ends:

```
worklog timesheet                  # the month that just finished
worklog timesheet --month 2026-08
worklog timesheet --all            # every month with data
```

48 half-hour rows by the month's real days, an **x** where the machine saw work, with
per-slot and per-day totals, hours, days worked, average and percentage of the month.
A slot is marked on any credited activity in it; excluded apps and paused stretches
leave no mark, and an open meeting window counts as presence.

Set `activity.sample_all_hours` to sample around the clock so evenings and weekends
reach the sheet. The daily report is unaffected — it clamps itself to your work hours,
which is what the after-hours addendum exists to complement.

Days that predate the sampler are rebuilt from their stored evidence — commits,
sessions and meetings — plus the times files were written on that day, which Spotlight
still knows long after the power log and login records have rotated away. That is the
only presence signal that survives after the fact, and it is restricted to your work
hours, since a machine left on overnight writes caches that say nothing about work.
It remains a **floor** on the hours rather than a measurement, and any sheet
containing such days says so at the top.

## Daily summary to a Teams chat

Optional, off by default. Work Buddy can put the day's **Work update** section into a
Microsoft Teams chat so it arrives as a plain message from you — no bot, no card frame.

```
worklog teams prepare      # repair the day if needed, then stage it
worklog teams send         # post it
worklog teams send --dry-run
```

Two agents, an hour apart, so there is a grace period. The first stages the summary
and notifies you; the second sends it. Turn the second off with `teams.auto_send` (or
the menu bar tick) and sending stays a click. Either way a degraded summary is never
staged in the first place, `teams skip` drops one day without disabling anything, and a
**paused** machine never sends — the summary stays staged for when you resume.

`teams.exclude_sections` drops whole sections from the message by heading, matched
loosely, for the parts of your log a manager has no use for.

Delivery goes through a Power Automate flow you create yourself — no tenant admin
consent needed. [docs/teams-daily-summary.md](docs/teams-daily-summary.md) is the full
build guide, including the four traps in the flow designer that are invisible from the
UI. Put the flow's URL in `~/.worklog/teams_url` (`chmod 600`; it is a bearer credential)
and set `teams.enabled`, then re-run `./install.sh` to get the morning agent.

Without a flow, a Teams deeplink is used instead: it pre-fills the compose box and you
press Enter. Put your own address in `~/.worklog/teams_recipient` for that fallback.

## Install

Requires macOS, Python 3.11+, the [Claude CLI](https://claude.com/claude-code) for
summarization, and [SwiftBar](https://github.com/swiftbar/SwiftBar) for the menu bar.

```bash
git clone <this repo> ~/.worklog
brew install --cask swiftbar terminal-notifier
cd ~/.worklog && ./install.sh
```

`install.sh` generates the three launchd agents for your account, creates
`config.json` from the example, installs a `worklog` shim on your `PATH`, and links the
menu bar plugin. The agents are generated rather than committed so no absolute paths end
up in the repo.

Optionally install [tokenwise](https://github.com/kushalsamani/tokenwise) into
`~/.claude-tools/tokenwise` (or point `tokenwise.dir` at your checkout): the daily log gains a
`Claude Code usage` block, the weekly rollup a usage summary, and the menu bar shows the live
context size. Nothing is parsed twice — Work Buddy reads tokenwise's SQLite ledger.

Then grant your `python3` binary **Accessibility** (to read window titles) and **Full Disk
Access** (if your log folder is inside a cloud-sync directory), and check the wiring:

```
worklog doctor
```

## Configuration

`config.json` is yours and is never committed; `config.example.json` is the template.
Everything specific to you lives there — your log folder, repo scan roots, author emails,
calendar feed, tracker project list, owner name.

Most of it is reachable from the menu bar: work hours, which sources are on, the pause
reminder interval, and a tick-list of apps to record or ignore. Apps can also be excluded
by vendor — the default configuration ignores every `com.apple.*` app except a handful,
so system apps do not clutter the log.

| Command | |
| --- | --- |
| `worklog report` | write today's log now |
| `worklog weekly` | merge the week's rows into one table |
| `worklog timesheet` | write the month's hours grid to the workbook |
| `worklog status` | current state as JSON (what the menu bar renders) |
| `worklog apps` | apps seen recently and whether each is recorded |
| `worklog config set work_hours.end 18:00` | change a setting |
| `worklog teams send` | post the staged summary to a Teams chat |
| `worklog doctor` | check every source and permission |

## Tests

```
python3 tests/test_worklog.py       # add -v to list what passed
```

They run against the real configuration and data on the machine, and skip rather than
fail when a source is not set up.

## Privacy

- Redaction patterns strip anything that looks like a secret before it is written down.
- Excluded apps leave no trace in the log: not the name, not the window title,
  not the time. The monthly timesheet is the one exception — inside your work
  hours it marks the slot, because the machine was demonstrably in use. It still
  records only that, never what was on screen.
- Window titles matching your ignore patterns are dropped.
- Paused stretches are absent from every source, not merely hidden in the summary:
  samples, commits, joined and booked meetings, Claude Code sessions and token usage,
  cloud files, shell history and exported conversations. The one source a pause cannot
  filter is the tracker export, whose rows carry a date but no time — those are tasks you
  typed onto the board yourself, not activity observed on this machine.
- The only outbound call is the summarization request; everything else is read locally.
