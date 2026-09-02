#!/bin/sh
# Install from a git checkout / source tree.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
ROOT=$(CDPATH= cd -- "$HERE/.." && pwd)
TARGET="${HOME}/.local/opt/StudyApp"
BIN="${HOME}/.local/bin"
APPS="${HOME}/.local/share/applications"

mkdir -p "$TARGET" "$BIN" "$APPS"
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
        --exclude '.git' --exclude '.venv' --exclude 'dist' --exclude 'build' \
        --exclude '__pycache__' --exclude 'tests' --exclude '.runtime' \
        "$ROOT/" "$TARGET/"
else
    (cd "$ROOT" && tar cf - \
        --exclude '.git' --exclude '.venv' --exclude 'dist' --exclude 'build' \
        --exclude '__pycache__' --exclude 'tests' --exclude '.runtime' .) \
        | (cd "$TARGET" && tar xf -)
fi
cp "$ROOT/packaging/linux/StudyApp.sh" "$TARGET/StudyApp.sh"
cp "$ROOT/packaging/linux/install.sh" "$TARGET/install.sh"
chmod +x "$TARGET/StudyApp.sh" "$TARGET/install.sh"

ln -sfn "$TARGET/StudyApp.sh" "$BIN/studyapp"

ICON="$TARGET/assets/icon.png"
[ -f "$ICON" ] || ICON=""

cat > "$APPS/studyapp.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=StudyApp
Comment=Hebrew study app for Bagrut and Meimad
Exec=$TARGET/StudyApp.sh
Icon=$ICON
Terminal=false
Categories=Education;
StartupNotify=true
EOF

printf '%s\n' "StudyApp הותקנה אל $TARGET"
printf '%s\n' "הפעלה: studyapp"
