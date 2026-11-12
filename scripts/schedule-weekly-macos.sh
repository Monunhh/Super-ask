#!/usr/bin/env bash
# Register (or remove) the weekly SuperAsk crawl on macOS, via launchd.
#
#   ./scripts/schedule-weekly-macos.sh            install: Sunday 02:00 local time
#   ./scripts/schedule-weekly-macos.sh 6 23 30    install: Saturday 23:30 (weekday 0=Sun..6=Sat)
#   ./scripts/schedule-weekly-macos.sh --uninstall
#
# The macOS counterpart of schedule-weekly.ps1. A per-user LaunchAgent, no admin
# rights. Each run: `npm run crawl:weekly` (priority 1 and 2 sources, change
# signals to the review queue), then rebuilds the per-site database in
# data/crawl/db/. It never writes data/kb/ and never changes an answer (FR-49).
# If the Mac is asleep at the scheduled time, launchd runs it on wake.
# Logs: var/monitor/logs/weekly.log

set -euo pipefail

LABEL="com.superask.crawl-weekly"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
  echo "Removed $LABEL"
  exit 0
fi

WEEKDAY="${1:-0}"
HOUR="${2:-2}"
MINUTE="${3:-0}"

NPM="$(command -v npm || true)"
[[ -n "$NPM" ]] || { echo "npm not found on PATH. Install Node.js first." >&2; exit 1; }
NODE_DIR="$(dirname "$(command -v node)")"

LOG_DIR="$ROOT/var/monitor/logs"
mkdir -p "$LOG_DIR" "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>WorkingDirectory</key><string>$ROOT</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-c</string>
    <string>echo "=== \$(date) ==="; "$NPM" run crawl:weekly; "$NPM" run build-site-db</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>$NODE_DIR:/usr/bin:/bin</string></dict>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key><integer>$WEEKDAY</integer>
    <key>Hour</key><integer>$HOUR</integer>
    <key>Minute</key><integer>$MINUTE</integer>
  </dict>
  <key>StandardOutPath</key><string>$LOG_DIR/weekly.log</string>
  <key>StandardErrorPath</key><string>$LOG_DIR/weekly.log</string>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
echo "Installed $LABEL: weekday $WEEKDAY at $(printf '%02d:%02d' "$HOUR" "$MINUTE")"
echo "Logs: $LOG_DIR/weekly.log"
echo "Run now: launchctl kickstart gui/$(id -u)/$LABEL"
