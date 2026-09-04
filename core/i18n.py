"""שפת עזר לתפריטים, שגיאות וסורק. השאלות נשארות בעברית."""
from __future__ import annotations

from typing import Any

LANGS: tuple[str, ...] = ("he", "en", "ru", "ar")
LANG_LABELS: dict[str, str] = {
    "he": "עברית",
    "en": "English",
    "ru": "Русский",
    "ar": "العربية",
}
PREF_KEY = "helper_lang"

_current = "he"

# he / en / ru / ar. מפתח קצר, בלי משפטים ארוכים בשאלות.
STRINGS: dict[str, dict[str, str]] = {
    "nav.home": {"he": "הבית", "en": "Home", "ru": "Главная", "ar": "الرئيسية"},
    "nav.exams": {"he": "מבחנים", "en": "Exams", "ru": "Экзамены", "ar": "امتحانات"},
    "nav.theory": {"he": "תאוריה", "en": "Theory", "ru": "Теория", "ar": "نظرية"},
    "nav.meimad": {"he": "מבחן מימד", "en": "Meimad exam", "ru": "Экзамен Меимад", "ar": "امتحان ميماد"},
    "nav.general": {"he": "מבחן כללי", "en": "General exam", "ru": "Общий экзамен", "ar": "امتحان عام"},
    "nav.mistakes": {"he": "הטעויות שלי", "en": "My mistakes", "ru": "Мои ошибки", "ar": "أخطائي"},
    "nav.ai": {
        "he": "העוזר שלי",
        "en": "My helper",
        "ru": "Помощник",
        "ar": "المساعد",
    },
    "nav.settings": {"he": "הגדרות", "en": "Settings", "ru": "Настройки", "ar": "الإعدادات"},
    "nav.about": {"he": "אודות", "en": "About", "ru": "О программе", "ar": "حول"},
    "settings.title": {"he": "הגדרות", "en": "Settings", "ru": "Настройки", "ar": "الإعدادات"},
    "settings.subtitle": {
        "he": "רק מה שמשפיע על הלמידה.",
        "en": "Only what changes how you learn.",
        "ru": "Только то, что влияет на учёбу.",
        "ar": "فقط ما يؤثر على التعلم.",
    },
    "settings.language": {
        "he": "שפת עזר",
        "en": "Helper language",
        "ru": "Язык подсказки",
        "ar": "لغة المساعدة",
    },
    "settings.hebrew_fix": {
        "he": "העברית הפוכה?",
        "en": "Hebrew backwards?",
        "ru": "Иврит наоборот?",
        "ar": "العبرية بالعكس؟",
    },
    "settings.hebrew_fix_hint": {
        "he": "במחשב רוסי/אנגלי השאירו «אוטומטי». אם משפטים הפוכים — אל תלחצו «תקן עברית» (זה מה שהופך אותם). רק אם האותיות עצמן הפוכות — «תקן אותיות».",
        "en": "On Russian/English Windows leave Auto. If sentences look reversed, do not tap Fix Hebrew (that flips them). Use Fix letters only if letters themselves are backwards.",
        "ru": "На русском/английском Windows оставьте «Авто». Если предложения перевёрнуты — не нажимайте «Исправить иврит». «Исправить буквы» только если перевёрнуты сами буквы.",
        "ar": "على ويندوز روسي/إنجليزي اترك تلقائي. إذا الجمل معكوسة لا تضغط «أصلح العبرية». «أصلح الحروف» فقط إذا الحروف نفسها معكوسة.",
    },
    "fix.auto": {"he": "אוטומטי", "en": "Auto", "ru": "Авто", "ar": "تلقائي"},
    "fix.words": {"he": "תקן עברית", "en": "Fix Hebrew", "ru": "Исправить иврит", "ar": "أصلح العبرية"},
    "fix.letters": {"he": "תקן אותיות", "en": "Fix letters", "ru": "Исправить буквы", "ar": "أصلح الحروف"},
    "fix.off": {"he": "כבוי", "en": "Off", "ru": "Выкл", "ar": "إيقاف"},
    "settings.language_hint": {
        "he": "התפריטים והתקלות בשפה הזו. השאלות נשארות בעברית.",
        "en": "Menus and errors use this language. Questions stay in Hebrew.",
        "ru": "Меню и ошибки на этом языке. Вопросы остаются на иврите.",
        "ar": "القوائم والأخطاء بهذه اللغة. الأسئلة تبقى بالعبرية.",
    },
    "settings.health": {"he": "בדיקת תקלות", "en": "Trouble check", "ru": "Проверка сбоев", "ar": "فحص الأعطال"},
    "settings.health_hint": {
        "he": "הסורק בודק לבד אם משהו שבור, מתקן מה שאפשר, ומסביר מה לעשות.",
        "en": "The scanner finds simple problems, repairs what it can, and tells you what to do.",
        "ru": "Сканер сам находит простые сбои, чинит что можно и говорит что делать.",
        "ar": "الماسح يفحص وحده، يصلح ما يستطيع، ويشرح ماذا تفعل.",
    },
    "settings.run_health": {
        "he": "הרץ בדיקת תקלות",
        "en": "Run trouble check",
        "ru": "Запустить проверку",
        "ar": "تشغيل الفحص",
    },
    "settings.look": {"he": "תצוגה", "en": "Look", "ru": "Вид", "ar": "المظهر"},
    "settings.updates": {"he": "עדכוני תוכנה", "en": "Updates", "ru": "Обновления", "ar": "التحديثات"},
    "btn.update_now": {"he": "עדכן עכשיו", "en": "Update now", "ru": "Обновить", "ar": "حدّث الآن"},
    "btn.check_update": {"he": "בדוק עדכון", "en": "Check update", "ru": "Проверить обновление", "ar": "تحقق من التحديث"},
    "btn.back": {"he": "חזרה", "en": "Back", "ru": "Назад", "ar": "رجوع"},
    "btn.next": {"he": "הבא", "en": "Next", "ru": "Далее", "ar": "التالي"},
    "btn.cancel": {"he": "ביטול", "en": "Cancel", "ru": "Отмена", "ar": "إلغاء"},
    "btn.ok": {"he": "אישור", "en": "OK", "ru": "ОК", "ar": "حسنًا"},
    "btn.hint": {"he": "רמז", "en": "Hint", "ru": "Подсказка", "ar": "تلميح"},
    "btn.check": {"he": "בדיקה", "en": "Check", "ru": "Проверить", "ar": "تحقق"},
    "btn.skip": {"he": "דלג", "en": "Skip", "ru": "Пропуск", "ar": "تخطي"},
    "btn.speak": {"he": "הקראה", "en": "Read aloud", "ru": "Озвучить", "ar": "قراءة"},
    "btn.explain": {
        "he": "הסבר בשפה שלי",
        "en": "Explain in my language",
        "ru": "Объясни на моём языке",
        "ar": "اشرح بلغتي",
    },
    "onboard.lang": {
        "he": "באיזו שפה נוח לקרוא תפריטים?",
        "en": "Which language is easier for menus?",
        "ru": "На каком языке удобнее меню?",
        "ar": "بأي لغة أسهل قراءة القوائم؟",
    },
    "onboard.welcome": {
        "he": "ברוכים הבאים ל-StudyApp",
        "en": "Welcome to StudyApp",
        "ru": "Добро пожаловать в StudyApp",
        "ar": "أهلًا بك في StudyApp",
    },
    "onboard.body": {
        "he": "רק שם וגיל. אחר כך מבחן קצר לקביעת הרמה.",
        "en": "Just name and age. Then a short test to set your level.",
        "ru": "Только имя и возраст. Потом короткий тест для уровня.",
        "ar": "الاسم والعمر فقط. بعد ذلك اختبار قصير للمستوى.",
    },
    "onboard.name": {"he": "שם", "en": "Name", "ru": "Имя", "ar": "الاسم"},
    "onboard.age": {"he": "גיל", "en": "Age", "ru": "Возраст", "ar": "العمر"},
    "onboard.id": {
        "he": "תעודת זהות (לא חובה)",
        "en": "ID number (optional)",
        "ru": "Номер удостоверения (необязательно)",
        "ar": "رقم الهوية (اختياري)",
    },
    "onboard.continue": {
        "he": "המשך למבחן אבחון",
        "en": "Continue to placement test",
        "ru": "К тесту уровня",
        "ar": "المتابعة لاختبار المستوى",
    },
    "onboard.need_name": {
        "he": "נא למלא שם וגיל",
        "en": "Please fill name and age",
        "ru": "Заполните имя и возраст",
        "ar": "املأ الاسم والعمر",
    },
    "dlg.update": {"he": "עדכון", "en": "Update", "ru": "Обновление", "ar": "تحديث"},
    "dlg.health": {"he": "בדיקת תקלות", "en": "Trouble check", "ru": "Проверка сбоев", "ar": "فحص الأعطال"},
    "health.ok": {
        "he": "הסורק בדק את StudyApp {version}. לא מצאתי תקלה. אם משהו עדיין תקוע: סגרו את התוכנה ופתחו שוב. אם גם זה לא עוזר, כבו את המחשב והדליקו.",
        "en": "The scanner checked StudyApp {version}. No problem found. If something is still stuck: close the app and open it again. If that fails, restart the computer.",
        "ru": "Сканер проверил StudyApp {version}. Сбоев нет. Если всё ещё зависает: закройте программу и откройте снова. Если не поможет — выключите компьютер и включите.",
        "ar": "الماسح فحص StudyApp {version}. لا مشكلة. إذا ما زال عالقًا: أغلق البرنامج وافتحه. إن لم ينفع، أعد تشغيل الحاسوب.",
    },
    "health.title": {
        "he": "בדיקת תקלות, גרסה {version}",
        "en": "Trouble check, version {version}",
        "ru": "Проверка сбоев, версия {version}",
        "ar": "فحص الأعطال، الإصدار {version}",
    },
    "health.fixed_head": {"he": "תיקנתי לבד:", "en": "I fixed:", "ru": "Исправил сам:", "ar": "أصلحت وحدي:"},
    "health.left_head": {"he": "מה שנשאר:", "en": "Still open:", "ru": "Что осталось:", "ar": "ما بقي:"},
    "health.do_head": {"he": "מה לעשות:", "en": "What to do:", "ru": "Что делать:", "ar": "ماذا تفعل:"},
    "health.reboot": {
        "he": "אם עדיין לא עובד: סגרו את התוכנה, ואם צריך כבו את המחשב והדליקו.",
        "en": "If it still fails: close the app, or restart the computer.",
        "ru": "Если всё ещё не работает: закройте программу или перезагрузите компьютер.",
        "ar": "إن لم يعمل بعد: أغلق البرنامج، أو أعد تشغيل الحاسوب.",
    },
    "health.data_created": {
        "he": "תיקיית הנתונים חסרה, יצרתי אותה מחדש.",
        "en": "The save folder was missing. I created it again.",
        "ru": "Папка сохранения пропала. Я создал её заново.",
        "ar": "مجلد الحفظ كان ناقصًا. أنشأته من جديد.",
    },
    "health.no_save": {
        "he": "אין גישה לתיקיית השמירה.",
        "en": "Cannot write to the save folder.",
        "ru": "Нет доступа к папке сохранения.",
        "ar": "لا يمكن الكتابة لمجلد الحفظ.",
    },
    "health.close_reopen": {
        "he": "סגרו את StudyApp לגמרי ופתחו אותה מחדש.",
        "en": "Fully close StudyApp and open it again.",
        "ru": "Полностью закройте StudyApp и откройте снова.",
        "ar": "أغلق StudyApp تمامًا وافتحه من جديد.",
    },
    "health.admin": {
        "he": "סגרו את התוכנה, פתחו אותה שוב בתור מנהל רק אם צריך, ואז נסו שוב.",
        "en": "Close the app. Open it again as administrator only if needed, then retry.",
        "ru": "Закройте программу. Откройте снова от имени администратора только если нужно.",
        "ar": "أغلق البرنامج. افتحه كمسؤول فقط إذا لزم، ثم أعد المحاولة.",
    },
    "health.profile_fixed": {
        "he": "קובץ הפרופיל היה פגום. שמרתי עותק ושחזרתי שמירה נקייה.",
        "en": "The profile file was broken. I saved a copy and started a clean save.",
        "ru": "Файл профиля был повреждён. Я сохранил копию и сделал чистое сохранение.",
        "ar": "ملف الملف الشخصي كان تالفًا. حفظت نسخة وبدأت حفظًا نظيفًا.",
    },
    "health.profile_bad": {
        "he": "קובץ הפרופיל פגום ואי אפשר לתקן אותו עכשיו.",
        "en": "The profile file is broken and cannot be fixed now.",
        "ru": "Файл профиля повреждён, сейчас не чинится.",
        "ar": "ملف الملف الشخصي تالف ولا يمكن إصلاحه الآن.",
    },
    "health.reboot_pc": {
        "he": "סגרו את התוכנה, הדליקו את המחשב מחדש, ואז פתחו את StudyApp.",
        "en": "Close the app, restart the computer, then open StudyApp.",
        "ru": "Закройте программу, перезагрузите компьютер, потом откройте StudyApp.",
        "ar": "أغلق البرنامج، أعد تشغيل الحاسوب، ثم افتح StudyApp.",
    },
    "health.no_questions": {
        "he": "חסרה תיקיית השאלות.",
        "en": "The questions folder is missing.",
        "ru": "Папка вопросов отсутствует.",
        "ar": "مجلد الأسئلة ناقص.",
    },
    "health.reinstall": {
        "he": "התקינו שוב את StudyApp מהקישור של המפתח. הלמידה השמורה לא נמחקת.",
        "en": "Install StudyApp again from the developer link. Saved learning is not deleted.",
        "ru": "Установите StudyApp снова по ссылке разработчика. Прогресс не удаляется.",
        "ar": "ثبّت StudyApp مرة أخرى من رابط المطوّر. التقدّم المحفوظ لا يُمسح.",
    },
    "health.bad_banks": {
        "he": "חלק מקבצי השאלות פגומים.",
        "en": "Some question files are broken.",
        "ru": "Часть файлов вопросов повреждена.",
        "ar": "بعض ملفات الأسئلة تالفة.",
    },
    "health.staging": {
        "he": "ניקיתי שאריות של עדכון ישן.",
        "en": "I cleaned leftover update files.",
        "ru": "Я почистил остатки старого обновления.",
        "ar": "نظّفت بقايا تحديث قديم.",
    },
    "health.font_fixed": {
        "he": "הפונט במחשב לא הציג עברית טוב. החלפתי לפונט שתומך בעברית.",
        "en": "The computer font did not show Hebrew well. I switched to a Hebrew-capable font.",
        "ru": "Шрифт компьютера плохо показывал иврит. Я сменил на шрифт с ивритом.",
        "ar": "الخط على الجهاز لم يعرض العبرية جيدًا. غيّرته لخط يدعم العبرية.",
    },
    "health.font_missing": {
        "he": "אין במחשב פונט עם עברית. לכן הטקסט יכול לצאת ריבועים.",
        "en": "This computer has no Hebrew font. Text may show as boxes.",
        "ru": "На компьютере нет шрифта с ивритом. Текст может быть квадратиками.",
        "ar": "لا يوجد خط عبري على الجهاز. قد يظهر النص مربعات.",
    },
    "health.display_fixed": {
        "he": "המחשב בשפה {os_lang}. התאמתי את כיוון העברית כדי שלא ייצא הפוך.",
        "en": "This computer is in {os_lang}. I adjusted Hebrew direction so it is not reversed.",
        "ru": "Этот компьютер на языке {os_lang}. Я поправил направление иврита, чтобы не было наоборот.",
        "ar": "هذا الحاسوب بلغة {os_lang}. عدّلت اتجاه العبرية حتى لا تنعكس.",
    },
    "health.utf8": {
        "he": "הגדרתי שמירה ב־UTF-8 כדי שעברית לא תישבר במחשב לא־עברי.",
        "en": "I set UTF-8 so Hebrew does not break on a non-Hebrew computer.",
        "ru": "Я включил UTF-8, чтобы иврит не ломался на не-ивритском компьютере.",
        "ar": "ضبطت UTF-8 حتى لا تنكسر العبرية على جهاز غير عبري.",
    },
    "health.crash": {
        "he": "בפעם הקודמת התוכנה נעצרה. ניקיתי את סימן הקריסה. אם זה חוזר: סגרו ופתחו, או כבו את המחשב.",
        "en": "Last time the app stopped. I cleared the crash mark. If it happens again: close and open, or restart the PC.",
        "ru": "В прошлый раз программа остановилась. Я убрал метку сбоя. Если повторится: закройте и откройте, или перезагрузите ПК.",
        "ar": "في المرة الماضية توقف البرنامج. مسحت علامة الانهيار. إن تكرر: أغلق وافتح، أو أعد تشغيل الجهاز.",
    },
    "health.stale_update": {
        "he": "הסרתי באנר עדכון ישן שכבר לא רלוונטי.",
        "en": "I removed an old update banner that no longer applies.",
        "ru": "Я убрал старый баннер обновления.",
        "ar": "أزلت شريط تحديث قديم لم يعد صالحًا.",
    },
    "health.update_hint": {
        "he": "אם ההורדה נכשלת: נסו שוב, או התקינו מקובץ. אפשר לשלוח להורה את הקישור.",
        "en": "If download fails: try again, or install from a file. You can send a parent the link.",
        "ru": "Если загрузка не вышла: попробуйте снова или поставьте из файла. Можно отправить ссылку родителю.",
        "ar": "إذا فشل التنزيل: أعد المحاولة أو ثبّت من ملف. يمكن إرسال الرابط لولي الأمر.",
    },
    "health.stuck": {
        "he": "ניסיתי לתקן פעמיים ולא נפתר. כבו את המחשב והדליקו. נשלחה הודעה שקטה למפתח, בלי שם.",
        "en": "I tried to fix this twice and it is still stuck. Restart the computer. A quiet note was sent to the developer, with no name.",
        "ru": "Я пытался исправить два раза — всё ещё сбой. Перезагрузите компьютер. Разработчику ушло тихое сообщение, без имени.",
        "ar": "حاولت الإصلاح مرتين وما زال عالقًا. أعد تشغيل الحاسوب. أُرسل تنبيه هادئ للمطوّر بلا اسم.",
    },
    "update.download_fail": {
        "he": "ההורדה נכשלה: {err}",
        "en": "Download failed: {err}",
        "ru": "Загрузка не удалась: {err}",
        "ar": "فشل التنزيل: {err}",
    },
    "update.manual": {
        "he": "אפשר להוריד ידנית:",
        "en": "You can download it by hand:",
        "ru": "Можно скачать вручную:",
        "ar": "يمكن التنزيل يدويًا:",
    },
    "update.no_url": {
        "he": "אין קישור הורדה. פורסם עמוד ההורדות, או התקינו מקובץ.",
        "en": "No download link. The download page was opened, or install from a file.",
        "ru": "Нет ссылки. Открыта страница загрузок, или поставьте из файла.",
        "ar": "لا يوجد رابط. فُتحت صفحة التنزيل، أو ثبّت من ملف.",
    },
    "explain.title": {
        "he": "הסבר בשפה שלי",
        "en": "Explain in my language",
        "ru": "Объяснение на моём языке",
        "ar": "شرح بلغتي",
    },
    "explain.body": {
        "he": "השאלה נשארת בעברית — ככה לומדים. קראו לאט. אם יש קטע קריאה, קראו אותו קודם. אחר כך בחרו תשובה. יש רמז אם תקועים. מילה קשה? בקשו מהורה או חבר.",
        "en": "The question stays in Hebrew — that is how you learn. Read slowly. If there is a passage, read it first. Then pick an answer. Use the hint if you are stuck. Hard word? Ask a parent or friend.",
        "ru": "Вопрос остаётся на иврите — так учат. Читайте медленно. Если есть текст, сначала его. Потом выберите ответ. Есть подсказка. Трудное слово? Спросите родителя или друга.",
        "ar": "السؤال يبقى بالعبرية — هكذا تتعلّم. اقرأ ببطء. إن وُجد نص، اقرأه أولًا. ثم اختر جوابًا. يوجد تلميح. كلمة صعبة؟ اسأل ولي الأمر أو صديقًا.",
    },
    "crash.boot": {
        "he": "מצאתי תקלה מהפעם הקודמת. תיקנתי מה שיכולתי. אם עדיין תקוע: סגרו את התוכנה, או כבו את המחשב והדליקו.",
        "en": "I found a problem from last time. I fixed what I could. If it is still stuck: close the app, or restart the computer.",
        "ru": "Нашёл сбой с прошлого раза. Исправил что смог. Если всё ещё плохо: закройте программу или перезагрузите компьютер.",
        "ar": "وجدت مشكلة من المرة الماضية. أصلحت ما استطعت. إن بقي عالقًا: أغلق البرنامج أو أعد تشغيل الحاسوب.",
    },
}


def normalize(code: str | None) -> str:
    raw = (code or "he").strip().lower()
    if raw.startswith("ru"):
        return "ru"
    if raw.startswith("ar"):
        return "ar"
    if raw.startswith("en"):
        return "en"
    if raw.startswith("he") or raw.startswith("iw"):
        return "he"
    return raw if raw in LANGS else "he"


def set_lang(code: str | None) -> str:
    global _current
    _current = normalize(code)
    return _current


def get_lang() -> str:
    return _current


def lookup(lang: str, key: str, **kwargs: Any) -> str:
    row = STRINGS.get(key) or {}
    text = row.get(normalize(lang)) or row.get("he") or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except Exception:
            pass
    return text


def t(key: str, **kwargs: Any) -> str:
    return lookup(_current, key, **kwargs)


def he(key: str, **kwargs: Any) -> str:
    return lookup("he", key, **kwargs)


def ui(key: str, **kwargs: Any) -> str:
    """עברית, ומתחת שפת העזר אם היא שונה."""
    primary = he(key, **kwargs)
    if _current == "he":
        return primary
    extra = t(key, **kwargs)
    if not extra or extra == primary:
        return primary
    return f"{primary}\n{extra}"


def block(key: str, **kwargs: Any) -> str:
    primary = he(key, **kwargs)
    if _current == "he":
        return primary
    extra = t(key, **kwargs)
    if not extra or extra == primary:
        return primary
    return f"{primary}\n\n{extra}"


def pair(hebrew: str, translated: str | None = None) -> str:
    if _current == "he" or not translated or translated == hebrew:
        return hebrew
    return f"{hebrew}\n{translated}"
