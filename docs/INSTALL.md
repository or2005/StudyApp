# התקנה והפצה של StudyApp 5.0.0

StudyApp היא תוכנת **דסקטופ**. אין גרסת דפדפן.

נתמך: **Windows 10, Windows 11**, ולינוקס (Ubuntu, Debian, Mint, Fedora, RHEL, Arch, Manjaro, openSUSE, Pop!_OS, Alpine, Raspberry Pi OS).

## Windows 10 / 11: ZIP (ההורדה הרשמית ל־5.0.0)

קישור ישיר:
https://github.com/or2005/StudyApp/releases/download/v5.0.0/StudyApp-5.0.0-windows.zip

1. הורידו `StudyApp-5.0.0-windows.zip`.
2. חלצו את **כל** התיקייה (לא רק את ה־exe).
3. הפעילו `StudyApp.exe`.

עמוד כל הגרסאות: https://github.com/or2005/StudyApp/releases/tag/v5.0.0

ההתקדמות נשמרת ב־`%LOCALAPPDATA%\StudyApp` (לא נמחקת כשמחליפים תיקייה).

אחרי ההתקנה: **הגדרות → עדכוני תוכנה**. אפשר לבדוק ברשת, להתקין מתוך התוכנה, או לבחור קובץ שהורדתם.

### קובץ התקנה (setup.exe)

ב־5.0.0 עדיין אין `setup.exe` ב־Release. אם יש אצלכם `StudyApp-4.9.0-setup.exe` מגרסה ישנה — עדיף לעבור ל־ZIP של 5.0.0.

## איך בונים את קובץ ההתקנה (למפתח)

פעם אחת במחשב Windows:

1. התקינו [Inno Setup 6](https://jrsoftware.org/isdl.php) (חינמי).
2. ודאו שקיים `dist\StudyApp\StudyApp.exe` (או שהסקריפט יבנה אותו).
3. הריצו:

```
powershell -File scripts\build_installer.ps1
```

הפלט: `dist\StudyApp-5.0.0-setup.exe` וגם עותק על שולחן העבודה.

אם Inno Setup לא מותקן, הסקריפט מנסה להתקין אותו עם `winget`.

## לינוקס: חבילה ניידת (מומלץ)

עובדת על כל ההפצות עם Python 3.10+ ו-Tkinter.

```
tar -xzf StudyApp-5.0.0-linux-portable.tar.gz
cd StudyApp
chmod +x StudyApp.sh install.sh
./StudyApp.sh
```

התקנה מערכתית (תפריט יישומים + פקודת `studyapp`):

```
./install.sh
```

הנתונים נשמרים: `~/.local/share/StudyApp`

### חבילות Tkinter לפי הפצה

| הפצה | התקנה |
|---|---|
| Ubuntu / Debian / Mint | `sudo apt install python3 python3-venv python3-tk python3-pip` |
| Fedora / RHEL | `sudo dnf install python3 python3-tkinter python3-pip` |
| Arch / Manjaro | `sudo pacman -S python python-pip tk` |
| openSUSE | `sudo zypper install python3 python3-tk python3-pip` |
| Alpine | `sudo apk add python3 py3-tkinter py3-pip` |

## למפתחים: בניית חבילות

```
python tools/build_release.py
```

- ב־Windows: zip ל־Windows 10/11 + tar.gz נייד ללינוקס
- ב־Linux: tar.gz מקומי + tar.gz נייד

GitHub Actions (`.github/workflows/build-packages.yml`) בונה את החבילות בכל תגית גרסה.
