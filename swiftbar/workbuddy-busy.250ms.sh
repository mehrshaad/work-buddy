#!/bin/sh
# Work Buddy — spinner shown only while a report, repair or summary is running.
#
# <xbar.title>Work Buddy (busy)</xbar.title>
# <xbar.desc>A spinner beside Work Buddy while it writes or sends something.</xbar.desc>
# <swiftbar.hideAbout>true</swiftbar.hideAbout>
# <swiftbar.hideRunInTerminal>true</swiftbar.hideRunInTerminal>
# <swiftbar.hideLastUpdated>true</swiftbar.hideLastUpdated>
# <swiftbar.hideDisablePlugin>true</swiftbar.hideDisablePlugin>
# <swiftbar.hideSwiftBar>true</swiftbar.hideSwiftBar>
#
# Separate from the main plugin and in plain sh on purpose: an animation needs a
# refresh every quarter second, and the main plugin costs ~0.4s of CPU a run. Idle,
# this is one directory listing. The engine writes ~/.worklog/busy/<pid> for the life
# of the run; no output hides the item.

dir="${WORKBUDDY_STATE:-$HOME/.worklog}/busy"
labels=""
for f in "$dir"/[0-9]*; do
  [ -f "$f" ] || continue
  # a run killed before its cleanup leaves its file behind; do not spin for it
  kill -0 "$(basename "$f")" 2>/dev/null || continue
  labels="$labels$(cat "$f")
"
done
[ -n "$labels" ] || exit 0

tick="${TMPDIR:-/tmp}/workbuddy-spin"
n=$(( ($(cat "$tick" 2>/dev/null || echo 0) + 1) % 10 ))
echo "$n" > "$tick"
frame=$(echo "⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏" | cut -d' ' -f$((n + 1)))

first=$(printf '%s' "$labels" | head -n 1)
echo "$frame ${first%% *}… | size=13"
echo "---"
printf '%s' "$labels" | while IFS= read -r l; do
  echo "${l}… | size=13"
done
