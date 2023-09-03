from typing import Union

import pygame
from engine.tools import Vector

from engine.file import JsonFile
from engine.timing import Clock
from engine.tools import Singleton


class Key:

    def __init__(self, key: int, repeat: (int, int), clock: Clock):
        self._key = key
        self._press = False
        self._hold = False
        self._state_mark = 0
        self._repeat = repeat[0]
        self._signal = clock.timer(repeat[1], periodic=True)

    def __getitem__(self, mode: str) -> bool:
        if mode == 'press':
            return self._press
        elif mode == 'hold':
            return self._hold

    def update(self, hold: tuple, now: int):
        if hold[self._key] - self._hold == 1:
            self._press = True
            self._state_mark = now
        elif hold[self._key]:
            if now - self._repeat > self._state_mark:
                self._press = self._signal.query()
            else:
                self._press = False
        else:
            self._press = False

        self._hold = hold[self._key]


class Mouse(metaclass=Singleton):

    def __init__(self):
        self._click = [False, False, False, False, False]
        self._release = [False, False, False, False, False]
        self._hold = [False, False, False, False, False]
        self._temp = self._click[:]
        self._drag = [Vector(0, 0), Vector(0, 0)]
        self._wheel = 0

        self.pos = Vector(pygame.mouse.get_pos())
        self.last_pos = Vector(pygame.mouse.get_pos())

    def __getitem__(self, button_mode: (int, str)) -> Union[bool, int]:
        if button_mode == "scroll":
            return self._wheel
        else:
            button, mode = button_mode
            if mode == "press":
                return self._click[button]
            elif mode == "hold":
                return self._hold[button]
            elif mode == "release":
                return self._release[button]

    def update(self, events: list):
        self._wheel = 0
        for event in events:
            if event.type == pygame.MOUSEWHEEL:
                self._wheel = event.y

        self.pos = Vector(pygame.mouse.get_pos())
        self._hold = pygame.mouse.get_pressed(num_buttons=5)

        if not self._hold[0]:
            self._drag[0] = Vector(self.pos)
        self._drag[1] = self._drag[0] - Vector(self.pos)

        self._click = [current - last == 1 for current, last in zip(self._hold, self._temp)]
        self._release = [current - last == -1 for current, last in zip(self._hold, self._temp)]
        self._temp = self._hold[:]

    def focused(self, rect: pygame.Rect):
        return rect.collidepoint(*self.pos)

    @property
    def drag(self) -> Vector:
        return Vector(self._drag[1])


class EventHandler(metaclass=Singleton):

    def __init__(self, clock: Clock, key_config: JsonFile):
        self.clock = clock
        self.mouse: Mouse = Mouse()

        keys = {key: pygame.key.key_code(value[0]) for key, value in key_config}
        delays = {key: value[1] for key, value in key_config}

        self.keys = self._generate_keys(keys, delays)
        self.events = None
        self.now = 0

    def _generate_keys(self, keys: dict, delays: dict) -> dict:
        return {key: Key(keys[key], delay, self.clock) for key, delay in delays.items()}

    def update(self):
        self.events = pygame.event.get()
        hold = pygame.key.get_pressed()
        self.now = self.clock.now
        self.mouse.update(self.events)

        for key in self.keys.values():
            key.update(hold, self.now)

    def text_input(self) -> str:
        for event in self.events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    return "BACKSPACE"
                elif event.key == pygame.K_RETURN:
                    return "RETURN"
                elif event.key == pygame.K_ESCAPE:
                    return "ESCAPE"
                else:
                    return event.unicode
        return ""

    def __getitem__(self, key_mode: (int, str)) -> Union[bool, str]:
        if key_mode == "exit":
            return any(event.type == pygame.QUIT for event in self.events)
        if key_mode == "type":
            return self.text_input()
        else:
            key, mode = key_mode
            return self.keys[key][mode]
