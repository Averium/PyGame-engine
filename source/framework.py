import pygame
from typing import Optional

from source.settings import COLORS, LAYOUT, KEYS, SETTINGS
from source.timing import Clock, Timer
from source.events import EventHandler
from source.tools import Singleton, Align, Filter
from source.gui import Gui, Button, DataLabel, WidgetGroup


class Framework(metaclass=Singleton):

    def __init__(self):

        # core framework elements #
        self.display = pygame.display.set_mode((LAYOUT.WIDTH, LAYOUT.HEIGHT), pygame.FULLSCREEN)
        self.clock = Clock()
        self.event_handler = EventHandler(self.clock, KEYS)

        # flow control #
        self.running = False
        self.fps = 0
        self.fps_filter = Filter(SETTINGS.FPS_FILTER, SETTINGS.FPS)

        # UI initialization #
        self.gui: Gui = Gui()

        self.exit_button: Optional[Button] = None
        self.fps_label: Optional[DataLabel] = None

        self.init_gui()

    def init_gui(self):
        main_group = WidgetGroup(self.gui, active=True, layer=1)

        settings = dict(text_size=20, align=Align.TL)
        self.fps_label = DataLabel(main_group, LAYOUT.FPS_LABEL, COLORS.GREY_LABEL, "FPS", **settings)

        settings = dict(text_size=32, align=Align.TL)
        self.exit_button = Button(main_group, LAYOUT.EXIT_BUTTON, COLORS.RED_BUTTON, "Close", **settings)

    def start(self):
        if not self.running:
            self.running = True
            self.loop()

    def exit(self):
        self.running = False

    def events(self):
        self.event_handler.update()

        if self.event_handler["EXIT", "press"] or self.event_handler["exit"] or self.exit_button.pressed:
            self.exit()

        self.gui.events(self.event_handler)

    def logic(self):
        self.fps_label.value = self.fps

    def render(self):
        self.display.fill(COLORS.BACKGROUND)
        self.gui.render(self.display)
        pygame.display.flip()

    def loop(self):
        while self.running:
            self.clock.tick(SETTINGS.FPS)
            self.fps = round(self.fps_filter(1 / self.clock.dt), 1)
            self.events()
            self.logic()
            self.render()

    def _debug_text(self, data=""):
        surface = Gui.FONT[False][20].render(str(data), False, COLORS.GREY7)
        rect = surface.get_rect()
        rect.topleft = (5, 5)
        self.display.blit(surface, rect)
