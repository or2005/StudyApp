import os
import sys
import unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.display import apply_display_quality, dip, enable_dpi_awareness, ui_scale


class DisplayQualityTests(unittest.TestCase):
    def test_enable_dpi_awareness_is_safe(self):
        self.assertIsInstance(enable_dpi_awareness(), bool)
        self.assertGreaterEqual(ui_scale(), 1.0)
        self.assertLessEqual(ui_scale(), 3.0)
        self.assertGreaterEqual(dip(20), 20)

    def test_tk_scaling_is_set_on_root(self):
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        try:
            scale = apply_display_quality(root)
            self.assertGreaterEqual(scale, 1.0)
            value = float(root.tk.call("tk", "scaling"))
            self.assertGreater(value, 0.8)
            self.assertLess(value, 8.0)
        finally:
            root.destroy()

    def test_skin_cards_match_requested_size(self):
        from ui.skin import _rounded_bytes
        from PIL import Image
        from io import BytesIO

        raw = _rounded_bytes(80, 48, 16, "#FFFFFF", False)
        img = Image.open(BytesIO(raw))
        self.assertEqual(img.size, (80, 48))


if __name__ == "__main__":
    unittest.main()
