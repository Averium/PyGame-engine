from os import getcwd
from os.path import join

from engine.file import JsonFile, DynamicJsonFile, IniFile
from engine.engine import Window


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

LAYOUT.WIDTH = Window.WIDTH
LAYOUT.HEIGHT = Window.HEIGHT
