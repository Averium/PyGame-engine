
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


class Filter:

    def __init__(self, coefficient: float, initial_value: float = 0.0):
        self._coefficient = min(max(coefficient, 0), 1)
        self._state = initial_value

    def __call__(self, value: float) -> float:
        self._state = self._state * (1 - self._coefficient) + value * self._coefficient
        return self._state
