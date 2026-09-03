# StudyApp

תוכנת לימוד בעברית לחלון שולחן עבודה. **Windows 10, Windows 11, ולינוקס** (Ubuntu, Debian, Fedora, Arch, openSUSE, Alpine ועוד). בלי דפדפן ובלי שרת.

**גרסה 4.6.1** · אור דדשב · dadshaev@gmail.com

## הורדה

| מערכת | קובץ |
|---|---|
| Windows 10 / 11 | `StudyApp-4.6.1-setup.exe` (קובץ התקנה) |
| כל לינוקס | `StudyApp-4.6.1-linux-portable.tar.gz` |

### Windows

לחצו פעמיים על `StudyApp-4.6.1-setup.exe` ועקבו אחרי האשף. אפשר גם לחלץ את ה-ZIP ולהפעיל `StudyApp.exe`.

### לינוקס

```
tar -xzf StudyApp-4.6.1-linux-portable.tar.gz
cd StudyApp
chmod +x StudyApp.sh
./StudyApp.sh
```

אם חסר Tkinter, לפי ההפצה:

```
sudo apt install python3 python3-venv python3-tk      # Ubuntu / Debian / Mint
sudo dnf install python3 python3-tkinter              # Fedora
sudo pacman -S python tk                              # Arch
sudo zypper install python3 python3-tk                # openSUSE
sudo apk add python3 py3-tkinter                      # Alpine
```

התקנה לתפריט: `./install.sh`

פירוט: [docs/INSTALL.md](docs/INSTALL.md)

## עדכונים

מההגדרות אפשר לבדוק עדכון ברשת, להתקין מתוך התוכנה, או לבחור קובץ `setup.exe` / ZIP שהורדתם. כברירת מחדל התוכנה בודקת לבד בהפעלה. ההתקדמות בלימוד לא נמחקת.

פינג אנונימי (גרסה ומערכת בלבד) כבוי כברירת מחדל. אפשר להדליק בהגדרות. שם, גיל ותעודת זהות לא נשלחים.

## למפתחים

```
pip install -r requirements.txt
python main.py
python -m unittest discover -s tests -p "test_*.py"
python tools/build_release.py
```

בלינוקס נוצר גם בינארי: `python tools/build_release.py --linux-binary`

## מקצועות

לשון, אנגלית, חשבון, היסטוריה, גאוגרפיה, אזרחות, כימיה, פיזיקה.

## רישיון

MIT. ראו `LICENSE`.
