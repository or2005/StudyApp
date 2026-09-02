#!/bin/sh
# Installs StudyApp for the current user on any common Linux desktop.
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TARGET="${HOME}/.local/opt/StudyApp"
BIN="${HOME}/.local/bin"
APPS="${HOME}/.local/share/applications"

mkdir -p "$TARGET" "$BIN" "$APPS"
# Copy everything except a previous runtime venv
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete --exclude '.runtime' --exclude '__pycache__' "$ROOT/" "$TARGET/"
else
    (cd "$ROOT" && tar cf - --exclude '.runtime' --exclude '__pycache__' .) | (cd "$TARGET" && tar xf -)
fi
chmod +x "$TARGET/StudyApp.sh" "$TARGET/install.sh" 2>/dev/null || true

ln -sfn "$TARGET/StudyApp.sh" "$BIN/studyapp"

ICON="$TARGET/assets/icon.png"
if [ ! -f "$ICON" ]; then
    ICON=""
fi

cat > "$APPS/studyapp.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=StudyApp
Name[he]=StudyApp
Comment=Hebrew study app for Bagrut and Meimad
Comment[he]=תוכנת לימוד לבגרות ומימ״ד
Exec=$TARGET/StudyApp.sh
Icon=$ICON
Terminal=false
Categories=Education;
StartupNotify=true
EOF

command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true

printf '%s\n' "StudyApp הותקנה אל $TARGET"
printf '%s\n' "הפעלה: studyapp   או מהתפריט StudyApp"
printf '%s\n' "אם הפקודה לא נמצאה — הוסיפו ~/.local/bin ל-PATH."
