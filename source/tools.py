
from typing import Tuple, Union, Iterator
from pygame.math import Vector2 as Vector


class Direction:
    UP = Vector(0, -1)
    DOWN = Vector(0, 1)
    LEFT = Vector(-1, 0)
    RIGHT = Vector(1, 0)


class Align:
    TL: str = "topleft"
    TR: str = "topright"
    BL: str = "bottomleft"
    BR: str = "bottomright"
    MT: str = "midtop"
    MB: str = "midbottom"
    ML: str = "midleft"
    MR: str = "midright"
    C: str = "center"


class Singleton(type):
    """
    Enhances a class, preventing the creation of multiple instances
    If an instance already exists upon class call, it returns that instance instead of creating a new one.
    """

    _INSTANCES = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._INSTANCES:
            cls._INSTANCES[cls] = super().__call__(*args, **kwargs)
        return cls._INSTANCES[cls]


class Hashable:
    _id = 0

    def __init__(self):
        self.id = self.unique_id()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: "Hashable") -> bool:
        return self.id == other.id

    @classmethod
    def unique_id(cls) -> str:
        cls._id += 1
        return f"{cls.__name__}_{cls._id}"


class LookupTable:

    def __init__(self, table: Tuple[Tuple[float]]):
        self._data: Tuple[float] = table[0]
        self._breakpoints: Tuple[float] = table[1]

    def __getitem__(self, key: Union[int, float]) -> float:
        left_bp, right_bp = self._find_closest_breakpoints(key)
        left_data = self._data[self._breakpoints.index(left_bp)]
        right_data = self._data[self._breakpoints.index(right_bp)]

        if left_bp == right_bp:
            return left_data

        value = left_data + (right_data - left_data) * (key - left_bp) / (right_bp - left_bp)

        return value

    def _find_closest_breakpoints(self, key: Union[int, float]) -> (int, int):
        left_breakpoint = self._breakpoints[0]
        right_breakpoint = self._breakpoints[-1]

        for bp in self._breakpoints:
            if bp <= key:
                left_breakpoint = bp
            else:
                right_breakpoint = bp
                break

        return left_breakpoint, right_breakpoint


class Filter:

    def __init__(self, coefficient: float, initial_value: float = 0.0):
        self._coefficient = min(max(coefficient, 0), 1)
        self._state = initial_value

    def __call__(self, value: float) -> float:
        self._state = self._state * (1 - self._coefficient) + value * self._coefficient
        return self._state


class SettingsIterator:

    def __init__(self, *args, **kwargs):
        self._index: int = 0
        longest = max([*kwargs.values(), args], key=lambda value: len(value) if hasattr(value, "__iter__") else 0)
        self._length = len(longest)

        self._args = tuple(arg if self.iterable(arg) else (arg,) * self._length for arg in args)
        self._kwargs = {name: kw if self.iterable(kw) else (kw,) * self._length for name, kw in kwargs.items()}

    def __iter__(self) -> Iterator:
        self._index = -1
        return self

    def __next__(self) -> Tuple[tuple, dict]:
        self._index += 1
        if self._index >= self._length:
            raise StopIteration
        args = tuple(value[self._index] for value in self._args)
        kwargs = {key: value[self._index] for key, value in self._kwargs.items()}
        return *args, kwargs

    @staticmethod
    def iterable(obj):
        return hasattr(obj, "__iter__")
