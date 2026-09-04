# התקנה והפצה של StudyApp 4.8.0

StudyApp היא תוכנת **דסקטופ**. אין גרסת דפדפן.

נתמך: **Windows 10, Windows 11**, ולינוקס (Ubuntu, Debian, Mint, Fedora, RHEL, Arch, Manjaro, openSUSE, Pop!_OS, Alpine, Raspberry Pi OS).

## Windows 10 / 11: קובץ התקנה (מומלץ)

1. הורידו `StudyApp-4.8.0-setup.exe`.
2. לחצו פעמיים, אשרו את האשף, סמנו קיצור לשולחן העבודה אם רוצים.
3. התוכנה תיפתח מהתפריט Start או מהקיצור.

הסרה: הגדרות Windows → יישומים → StudyApp → הסר.

ההתקדמות נשמרת ב־`%LOCALAPPDATA%\StudyApp` גם אחרי הסרה (לא נמחקת).

אחרי ההתקנה: **הגדרות → עדכוני תוכנה**. אפשר לבדוק ברשת, להתקין מתוך התוכנה, או לבחור קובץ שהורדתם. כברירת מחדל התוכנה בודקת לבד בהפעלה.

### בלי מתקין: ZIP

1. הורידו `StudyApp-4.8.0-windows.zip`.
2. חלצו את **כל** התיקייה.
3. הפעילו `StudyApp.exe`.

## איך בונים את קובץ ההתקנה (למפתח)

פעם אחת במחשב Windows:

1. התקינו [Inno Setup 6](https://jrsoftware.org/isdl.php) (חינמי).
2. ודאו שקיים `dist\StudyApp\StudyApp.exe` (או שהסקריפט יבנה אותו).
3. הריצו:

```
powershell -File scripts\build_installer.ps1
```

הפלט: `dist\StudyApp-4.8.0-setup.exe` וגם עותק על שולחן העבודה.

אם Inno Setup לא מותקן, הסקריפט מנסה להתקין אותו עם `winget`.

## לינוקס: חבילה ניידת (מומלץ)

עובדת על כל ההפצות עם Python 3.10+ ו-Tkinter.

```
tar -xzf StudyApp-4.8.0-linux-portable.tar.gz
cd StudyApp
chmod +x StudyApp.sh install.sh
./StudyApp.sh
```

התקנה למשתמש (תפריט יישומים + פקודה `studyapp`):

```
./install.sh
```

ההתקדמות: `~/.local/share/StudyApp`

### חבילת Tkinter לפי הפצה

| הפצה | פקודה |
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

- ב-Windows: zip ל-Windows 10/11 + tar.gz נייד ללינוקס
- ב-Linux: tar.gz בינארי + tar.gz נייד

GitHub Actions (`.github/workflows/build-packages.yml`) בונה את שלושת סוגי הקבצים.
