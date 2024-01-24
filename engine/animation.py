import json
from typing import Optional, Tuple

import pygame


class SpriteSheet:

    IMAGE_EXTENSION = "png"
    DATA_EXTENSION = "json"

    def __init__(self, filename: str, scale: int = 1):

        self._image: Optional[pygame.Surface] = None
        self._data = dict()
        self._frames = {True: {}, False: {}}
        self._scale = scale

        image_path = f"{filename}.{SpriteSheet.IMAGE_EXTENSION}"
        meta_path = f"{filename}.{SpriteSheet.DATA_EXTENSION}"

        self._image = pygame.image.load(image_path).convert_alpha()

        with open(meta_path, 'r') as F:
            self._data = json.load(F)

        for name, index in self._data["frames"].items():
            frame = pygame.Surface(index[2:], pygame.SRCALPHA, 32).convert_alpha()
            frame.blit(self._image, (0, 0), index)
            frame = pygame.transform.scale(frame, (index[2] * self._scale, index[3] * self._scale))
            self._frames[False][name] = frame
            self._frames[True][name] = pygame.transform.flip(frame, True, False)

    def size(self, key: str) -> (int, int):
        return self._data["frames"][key][2:]

    def get(self, key, flipped: bool = False) -> pygame.Surface:
        return self._frames[flipped][key]


class Scene:

    def __init__(self, sprite_sheet: SpriteSheet, keys: Tuple):
        self._sheet = sprite_sheet
        self._keys = keys

        self._turnaround = len(keys) - 1
        self._index = 0

    def next(self):
        self._index = self._index + 1 if self._index < self._turnaround else 0

    def reset(self):
        self._index = 0

    def frame(self, flipped: bool = False):
        key = self._keys[self._index]
        return self._sheet.get(key, flipped)


class Animation:

    def __init__(self, sprite_sheet, period: int = 150):
        pass
