#!/usr/bin/env bash
# Work Buddy installer: writes the launchd agents for this machine and account.
# The agents are generated rather than committed, so no absolute paths or usernames
# ever land in the repo.
set -euo pipefail

ROOT="${WORKBUDDY_HOME:-$HOME/.worklog}"
PY="$(command -v python3)"
AGENTS="$HOME/Library/LaunchAgents"
PATH_LINE="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$HOME/.local/bin:$HOME/.claude/local"

mkdir -p "$AGENTS" "$ROOT/logs" "$HOME/.local/bin"

if [ ! -f "$ROOT/config.json" ]; then
  cp "$ROOT/config.example.json" "$ROOT/config.json"
  echo "created $ROOT/config.json from the example — edit it before the first report"
fi

printf '#!/bin/sh\nexec %s %s/bin/worklog.py "$@"\n' "$PY" "$ROOT" > "$HOME/.local/bin/worklog"
chmod +x "$HOME/.local/bin/worklog"

agent() {  # label, schedule-xml, args...
  local label="$1" sched="$2"; shift 2
  local args=""
  for a in "$@"; do args="$args    <string>$a</string>\n"; done
  cat > "$AGENTS/$label.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>$label</string>
  <key>ProgramArguments</key><array>
    <string>$PY</string>
    <string>$ROOT/bin/worklog.py</string>
$(printf "$args")  </array>
$sched
  <key>EnvironmentVariables</key><dict>
    <key>PATH</key><string>$PATH_LINE</string>
    <key>HOME</key><string>$HOME</string>
  </dict>
  <key>ProcessType</key><string>Background</string>
  <key>StandardOutPath</key><string>$ROOT/logs/$label.out</string>
  <key>StandardErrorPath</key><string>$ROOT/logs/$label.err</string>
</dict></plist>
PLIST
  launchctl bootout "gui/$(id -u)/$label" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$AGENTS/$label.plist"
  echo "installed $label"
}

weekdays_at() {  # hour -> StartCalendarInterval for Mon-Fri
  printf '  <key>StartCalendarInterval</key>\n  <array>\n'
  for d in 1 2 3 4 5; do
    printf '    <dict><key>Weekday</key><integer>%s</integer><key>Hour</key><integer>%s</integer><key>Minute</key><integer>0</integer></dict>\n' "$d" "$1"
  done
  printf '  </array>\n  <key>RunAtLoad</key><false/>\n'
}

agent com.workbuddy.tracker "$(printf '  <key>StartInterval</key><integer>60</integer>\n  <key>RunAtLoad</key><true/>\n')" sample
agent com.workbuddy.summarize "$(weekdays_at 17)" report
agent com.workbuddy.catchup "$(weekdays_at 10)" repair

PLUGINS="$HOME/Library/Application Support/SwiftBar/Plugins"
if [ -d "$PLUGINS" ]; then
  ln -sf "$ROOT/swiftbar/workbuddy.10s.py" "$PLUGINS/workbuddy.10s.py"
  echo "linked the SwiftBar plugin"
else
  echo "SwiftBar not found — install it with: brew install --cask swiftbar"
fi

echo
echo "Done. Grant Accessibility and Full Disk Access to: $PY"
echo "Then check with: worklog doctor"
