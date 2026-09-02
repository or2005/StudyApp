"""PyInstaller: DPI לפני כל ייבוא Tk, כדי שהחלון לא יומתח מטושטש."""
from core.display import enable_dpi_awareness

enable_dpi_awareness()
