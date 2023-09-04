from abc import ABC, abstractmethod

import pygame

from engine.timing import Clock
from engine.tools import Window, Singleton


class Engine(ABC, metaclass=Singleton):

    def __init__(self, fps, display_flags=pygame.FULLSCREEN):

        self.display = pygame.display.set_mode((Window.WIDTH, Window.HEIGHT), display_flags, vsync=1)
        self.clock = Clock()
        self._running = False
        self._fps = fps

    def start(self):
        if not self._running:
            self._running = True
            self.loop()

    def exit(self):
        self._running = False

    @abstractmethod
    def events(self):
        pass

    @abstractmethod
    def logic(self):
        pass

    @abstractmethod
    def render(self):
        pass

    def loop(self):
        while self._running:
            self.clock.tick(self._fps)
            self.events()
            self.logic()
            self.render()
