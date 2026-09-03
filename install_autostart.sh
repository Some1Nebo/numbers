#!/bin/bash
# Install the Numbers Workout .app bundle and register it to start at login.
#
# Usage:  ./install_autostart.sh
#
# - Copies dist/"Numbers Workout.app" to ~/Applications/
# - Writes ~/Library/LaunchAgents/com.sergey.numbers-workout.plist (RunAtLoad)
# - (Re)starts it via launchctl, so the menu bar icon appears immediately
#
# To remove autostart:
#   launchctl bootout gui/$(id -u)/com.sergey.numbers-workout
#   rm ~/Library/LaunchAgents/com.sergey.numbers-workout.plist
set -euo pipefail

APP_NAME="Numbers Workout"
LABEL="com.sergey.numbers-workout"
SRC_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST_DIR="$HOME/Applications"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
APP_SRC="$SRC_DIR/dist/$APP_NAME.app"

if [ ! -d "$APP_SRC" ]; then
    echo "Not found: $APP_SRC"
    echo "Build it first:  .venv/bin/pyinstaller --noconfirm --clean --onedir --windowed \\"
    echo "  --name \"$APP_NAME\" --icon app_icon.icns --info-plist info.plist.json \\"
    echo "  --add-data \"menubar_icon.png:.\" menubar.py"
    exit 1
fi

# Stop any running instance (launchd-managed or manual)
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
pkill -f "$DEST_DIR/$APP_NAME.app/Contents/MacOS/$APP_NAME" 2>/dev/null || true

mkdir -p "$DEST_DIR" "$HOME/Library/Logs"
rm -rf "$DEST_DIR/$APP_NAME.app"
cp -R "$APP_SRC" "$DEST_DIR/"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$DEST_DIR/$APP_NAME.app/Contents/MacOS/$APP_NAME</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/numbers-workout.out.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/numbers-workout.err.log</string>
</dict>
</plist>
EOF

launchctl bootstrap "gui/$(id -u)" "$PLIST"

echo "Installed:    $DEST_DIR/$APP_NAME.app"
echo "Autostart:    $PLIST (starts at every login)"
echo "Logs:         ~/Library/Logs/numbers-workout.{out,err}.log"
