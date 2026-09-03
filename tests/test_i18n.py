import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core import i18n, textfix


class I18nTests(unittest.TestCase):
    def tearDown(self):
        i18n.set_lang("he")

    def test_helper_languages_cover_nav(self):
        for lang in i18n.LANGS:
            i18n.set_lang(lang)
            self.assertTrue(i18n.t("nav.settings"))
            self.assertTrue(i18n.t("health.ok", version="4.6.0"))

    def test_ui_is_bilingual_when_helper_is_not_hebrew(self):
        i18n.set_lang("ru")
        text = i18n.ui("nav.home")
        self.assertIn("הבית", text)
        self.assertIn("Главная", text)
        i18n.set_lang("he")
        self.assertEqual(i18n.ui("nav.home"), "הבית")

    def test_guess_helper_maps_known_os(self):
        self.assertIn(textfix.guess_helper(), {"he", "en", "ru", "ar"})

    def test_normalize(self):
        self.assertEqual(i18n.normalize("RU-ru"), "ru")
        self.assertEqual(i18n.normalize("iw"), "he")
        self.assertEqual(i18n.normalize("unknown"), "he")


if __name__ == "__main__":
    unittest.main()
