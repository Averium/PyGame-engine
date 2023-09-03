from os import getcwd
from os.path import join

from engine.file import JsonFile, DynamicJsonFile, IniFile

# resolution fix ---------------------------------------------------------------------
from ctypes import windll
windll.user32.SetProcessDPIAware()
WIDTH, HEIGHT = (windll.user32.GetSystemMetrics(0), windll.user32.GetSystemMetrics(1))
# ------------------------------------------------------------------------------------


class PATH:
    ROOT = getcwd()
    DATA = join(ROOT, "data")

    LAYOUT = join(DATA, "layout")
    COLORS = join(DATA, "colors")
    SETTINGS = join(DATA, "settings")
    KEYBIND = join(DATA, "keybind")


SETTINGS = IniFile(PATH.SETTINGS, read_only=False)
LAYOUT = DynamicJsonFile(PATH.LAYOUT)
KEYS = JsonFile(PATH.KEYBIND)
COLORS = DynamicJsonFile(PATH.COLORS)

LAYOUT.WIDTH = WIDTH
LAYOUT.HEIGHT = HEIGHT
