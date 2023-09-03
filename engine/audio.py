from typing import Tuple

import pygame

from engine.tools import Singleton

pygame.mixer.init()


class Sound(pygame.mixer.Sound):

    def __init__(self, filepath, volume=0.1):
        super().__init__(filepath)
        self.set_volume(volume)


class Audio(metaclass=Singleton):

    def __init__(self, sound_data: dict):
        self.enabled = False
        self._sounds = {name: Sound(filename) for name, filename in sound_data.items()}

    def play(self, key):
        pass

    def set_volume(self, value, sounds: Tuple[str]):
        pass
