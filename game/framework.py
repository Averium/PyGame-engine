from typing import Optional

import pygame

from engine import Engine
from engine import EventHandler
from engine.animation import SpriteSheet, Scene
from engine.gui import Gui, WidgetGroup, Button, DataLabel, TextLabel, HorizontalSlider, VerticalSlider, NumericInput
from engine.timing import Timer
from engine.tools import Align, Filter
from game.settings import COLORS, LAYOUT, KEYS, SETTINGS, PATH


class Framework(Engine):

    def __init__(self):
        super().__init__(SETTINGS.FPS, SETTINGS.SCALE, pygame.FULLSCREEN | pygame.SCALED)

        self.event_handler = EventHandler(self.clock, KEYS)

        self.fps = 0
        self.fps_filter = Filter(SETTINGS.FPS_FILTER, SETTINGS.FPS)

        self.gui: Gui = Gui(text_size=16)

        self.exit_button: Optional[Button] = None
        self.fps_label: Optional[DataLabel] = None

        self.test_slider_1: Optional[VerticalSlider] = None
        self.test_slider_2: Optional[VerticalSlider] = None
        self.test_input: Optional[NumericInput] = None

        self.test_timer = Timer(self.clock, 150, periodic=True)
        # self.test_sprite_sheet = SpriteSheet(PATH.TEST_SPRITE, scale=1)
        # self.test_scene = Scene(self.test_sprite_sheet, ("machinegun_run_1", "machinegun_run_2"))

        self.init_gui()

    def init_gui(self):
        main_group = WidgetGroup(self.gui, active=True, layer=2)

        settings = dict(text_size=28, align=Align.TL, decimals=1)
        self.fps_label = DataLabel(main_group, LAYOUT.FPS_LABEL, COLORS.GREY_LABEL, "FPS", **settings)
        settings = dict(text_size=28, align=Align.TL)
        self.exit_button = Button(main_group, LAYOUT.EXIT_BUTTON, COLORS.RED_BUTTON, "Close", **settings)

        settings = dict(text="Test", text_size=28, align=Align.TL, decimals=1)
        self.test_slider_1 = VerticalSlider(main_group, LAYOUT.TEST_SLIDER_1, COLORS.RED_SLIDER, 200, register="test")
        self.test_slider_2 = VerticalSlider(main_group, LAYOUT.TEST_SLIDER_2, COLORS.RED_SLIDER, 200, register="test")
        self.test_input = NumericInput(main_group, LAYOUT.TEST_INPUT, COLORS.RED_INPUT, register="test", **settings)

    def events(self):
        self.event_handler.update()

        if self.event_handler["EXIT", "press"] or self.event_handler["exit"] or self.exit_button.pressed:
            self.exit()

        self.gui.events(self.event_handler)

    def logic(self):
        # self.fps_label.value = self.fps_filter(1 / self.clock.dt)
        # if self.test_timer.query():
        #     self.test_scene.next()
        pass

    def render(self):
        self.display.fill(COLORS.BACKGROUND)
        self.gui.render(self.display)
        # self.display.blit(self.test_scene.frame(False), (100, 100))
        pygame.display.flip()

    def debug_text(self, data=""):
        surface = Gui.FONT[False][20].render(str(data), False, COLORS.GREY7)
        rect = surface.get_rect()
        rect.topleft = (5, 5)
        self.display.blit(surface, rect)
