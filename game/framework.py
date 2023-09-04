from typing import Optional

import pygame

from engine import Engine
from engine import EventHandler
from engine.gui import Gui, Button, DataLabel, WidgetGroup, FloatingWindow
from engine.tools import Align, Filter
from game.settings import COLORS, LAYOUT, KEYS, SETTINGS


class Framework(Engine):

    def __init__(self):
        super().__init__(SETTINGS.FPS, pygame.FULLSCREEN | pygame.SCALED)

        self.event_handler = EventHandler(self.clock, KEYS)

        self.fps = 0
        self.fps_filter = Filter(SETTINGS.FPS_FILTER, SETTINGS.FPS)

        self.gui: Gui = Gui()

        self.exit_button: Optional[Button] = None
        self.debug_button: Optional[Button] = None
        self.fps_label: Optional[DataLabel] = None
        self.debug_window: Optional[FloatingWindow] = None

        self.init_gui()

    def init_gui(self):
        main_group = WidgetGroup(self.gui, active=True, layer=2)

        self.debug_window = FloatingWindow(self.gui, LAYOUT.DEBUG_WINDOW, COLORS.WINDOW, "Debug", layer=1)

        settings = dict(text_size=20, align=Align.TL, decimals=1)
        self.fps_label = DataLabel(main_group, LAYOUT.FPS_LABEL, COLORS.GREY_LABEL, "FPS", **settings)

        settings = dict(text_size=32, align=Align.TL)
        self.exit_button = Button(main_group, LAYOUT.EXIT_BUTTON, COLORS.RED_BUTTON, "Close", **settings)
        self.debug_button = Button(main_group, LAYOUT.DEBUG_BUTTON, COLORS.GREY_BUTTON, "Debug", **settings)

    def events(self):
        self.event_handler.update()

        if self.event_handler["EXIT", "press"] or self.event_handler["exit"] or self.exit_button.pressed:
            self.exit()

        self.gui.events(self.event_handler)
        if self.debug_button.pressed:
            self.gui.activate_group(self.debug_window)

    def logic(self):
        self.fps_label.value = self.fps_filter(1 / self.clock.dt)

    def render(self):
        self.display.fill(COLORS.BACKGROUND)
        self.gui.render(self.display)
        pygame.display.flip()

    def debug_text(self, data=""):
        surface = Gui.FONT[False][20].render(str(data), False, COLORS.GREY7)
        rect = surface.get_rect()
        rect.topleft = (5, 5)
        self.display.blit(surface, rect)
