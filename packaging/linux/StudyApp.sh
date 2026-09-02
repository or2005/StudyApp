#!/bin/sh
# StudyApp — launcher for Ubuntu, Debian, Fedora, Arch, openSUSE, Mint, Alpine, …
set -eu

ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$ROOT"

say() { printf '%s\n' "$*"; }

find_python() {
    if command -v python3 >/dev/null 2>&1; then
        printf '%s\n' "python3"
        return 0
    fi
    if command -v python >/dev/null 2>&1; then
        printf '%s\n' "python"
        return 0
    fi
    return 1
}

tk_help() {
    id=""
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        id=${ID:-}
    fi
    say ""
    say "חסרה תמיכת חלונות (Tkinter). התקינו לפי ההפצה:"
    case "$id" in
        debian|ubuntu|linuxmint|pop|elementary|raspbian)
            say "  sudo apt update && sudo apt install -y python3 python3-venv python3-tk python3-pip fonts-noto-core"
            ;;
        fedora|rhel|centos|rocky|almalinux)
            say "  sudo dnf install -y python3 python3-tkinter python3-pip google-noto-sans-fonts"
            ;;
        arch|manjaro|endeavouros)
            say "  sudo pacman -S --needed python python-pip tk noto-fonts"
            ;;
        opensuse*|suse)
            say "  sudo zypper install -y python3 python3-tk python3-pip google-noto-fonts"
            ;;
        alpine)
            say "  sudo apk add python3 py3-tkinter py3-pip font-noto"
            ;;
        *)
            say "  Debian/Ubuntu: sudo apt install python3 python3-venv python3-tk"
            say "  Fedora:        sudo dnf install python3 python3-tkinter"
            say "  Arch:          sudo pacman -S python tk"
            say "  openSUSE:      sudo zypper install python3 python3-tk"
            say "  Alpine:        sudo apk add python3 py3-tkinter"
            ;;
    esac
}

if ! PY=$(find_python); then
    say "לא נמצא Python 3 במחשב."
    tk_help
    exit 1
fi

if ! "$PY" -c "import tkinter" >/dev/null 2>&1; then
    tk_help
    exit 1
fi

VENV="$ROOT/.runtime"
PIP_OK=0
if [ -x "$VENV/bin/python" ]; then
    if "$VENV/bin/python" -c "import customtkinter" >/dev/null 2>&1; then
        PIP_OK=1
    fi
fi

if [ "$PIP_OK" -eq 0 ]; then
    say "מתקין תלויות מקומיות (פעם אחת)..."
    "$PY" -m venv "$VENV"
    "$VENV/bin/python" -m pip install --upgrade pip -q
    "$VENV/bin/python" -m pip install -r "$ROOT/requirements.txt"
fi

export PYTHONPATH="$ROOT"
exec "$VENV/bin/python" "$ROOT/main.py" "$@"
