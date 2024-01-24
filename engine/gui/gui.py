from abc import ABC, abstractmethod
from enum import Enum
from math import floor
from typing import Optional, Union, Tuple, List, Iterator, Any

import pygame

from engine.events import EventHandler
from engine.tools import Align
from engine.tools import Singleton, Hashable
from engine.tools import Vector

RectangleArrayType = Union[Tuple, List]
CoordinateArrayType = Union[Vector, Tuple, List]


class WidgetSettingsIterator:

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


class WidgetStyleDescriptor:
    pass


class Register:

    def __init__(self, value: Any = None):
        self.value: Any = value

    def __bool__(self) -> bool: return bool(self.value)

    def __int__(self) -> int: return int(self.value)

    def __float__(self) -> float: return float(self.value)

    def __str__(self) -> str: return str(self.value)


class Gui(metaclass=Singleton):

    pygame.font.init()
    FONT_SIZES = (12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32)
    FONT = {
        False: {size: pygame.font.SysFont("monospace", size, bold=False) for size in FONT_SIZES},
        True: {size: pygame.font.SysFont("monospace", size, bold=True) for size in FONT_SIZES},
    }

    def __init__(self, text_size: int = 20):
        self._text_size = text_size
        self._all_groups = set()
        self._active_groups = set()
        self._focused = set()
        self._registers = dict()

    @property
    def text_size(self):
        return min(Gui.FONT_SIZES, key=lambda element: abs(element - self._text_size))

    def register(self, name: str = None, value: Any = None):
        if name is None:
            return Register(value)
        elif name not in self._registers.keys():
            self._registers[name] = Register(value=value)
        elif self._registers[name].value is None:
            self._registers[name].value = value
        return self._registers[name]

    def add_group(self, *groups: "WidgetGroup"):
        self._all_groups.update(groups)

    def is_active(self, item: Union["Widget", "WidgetGroup"]):
        if isinstance(item, WidgetGroup):
            return item in self._active_groups
        else:
            return any(item in group for group in self._active_groups)

    def is_focused(self, item: Union["Widget", "WidgetGroup"] = None):
        if item is None:
            return bool(self._focused)
        elif isinstance(item, WidgetGroup):
            return item in self._focused or any(widget in self._focused for widget in item)
        else:
            return item in self._focused

    def activate_group(self, *groups: "WidgetGroup"):
        self._active_groups |= set(groups)

    def deactivate_group(self, *groups: "WidgetGroup"):
        self._active_groups -= set(groups)

    def focus_widget(self, item: Union["Widget", "WidgetGroup"], overwrite: bool = False):
        if (not self._focused or overwrite) and self.is_active(item):
            self._focused = {item}

    def release_widget(self, item: Union["Widget", "WidgetGroup"], event_handler: EventHandler = None):
        if item in self._focused:
            self._focused.remove(item)
            if event_handler is not None:
                self.events(event_handler)

    def events(self, event_handler: EventHandler):
        active = self._focused if self._focused else self._active_groups
        for group in sorted(active, key=lambda g: g.layer, reverse=True):
            group.events(event_handler)

    def render(self, display: pygame.Surface):
        for group in sorted(self._active_groups, key=lambda g: g.layer, reverse=True):
            group.render(display)


class Widget(Hashable, pygame.Rect, ABC):

    def __init__(
            self,
            group: Optional["WidgetGroup"],
            dim: RectangleArrayType,
            anchor: CoordinateArrayType = None,
            align: str = Align.TL,
            layer: int = 1,
            **kwargs,
    ):
        pygame.Rect.__init__(self, dim)
        Hashable.__init__(self)

        self._layer = layer
        self._base = Vector(0, 0)
        self._anchor = Vector(0, 0)
        self._align = None

        self.snap(dim[:2], anchor, align)

        self.hovered = False
        self.entered = False
        self.leaved = False
        self.pressed = False
        self.pressed_elsewhere = False
        self.last_hovered = False

        if group is not None:
            self._gui = group.gui
            group.add_widget(self)

    def snap(self, pos: CoordinateArrayType = None, anchor: CoordinateArrayType = None, align: str = None):
        if pos is not None:
            self._base = Vector(pos)
        if anchor is not None:
            self._anchor = Vector(anchor)
        if align is not None:
            self._align = align

        setattr(self, self._align, self._base + self._anchor)

    def events(self, event_handler: EventHandler):
        self.hovered = event_handler.mouse.focused(self)
        self.entered = self.hovered and not self.last_hovered
        self.leaved = self.last_hovered and not self.hovered
        self.pressed = self.hovered and event_handler.mouse[0, "press"]
        self.pressed_elsewhere = not self.hovered and event_handler.mouse[0, "press"]
        self.last_hovered = self.hovered

    @property
    def layer(self) -> int:
        return self._layer

    @abstractmethod
    def render(self, display: pygame.Surface) -> None:
        pass


class WidgetGroup(Hashable):

    def __init__(
            self,
            gui: Gui,
            active: bool = False,
            layer: int = 1
    ):
        Hashable.__init__(self)
        self._gui = gui
        self._widgets = set()
        self._layer = layer

        gui.add_group(self)
        if active:
            gui.activate_group(self)

    def __iter__(self) -> Widget:
        yield from sorted(self._widgets, key=lambda widget: widget.layer, reverse=True)

    @property
    def layer(self):
        return self._layer

    @property
    def gui(self):
        return self._gui

    def add_widget(self, widget: Widget):
        self._widgets.add(widget)

    def events(self, event_handler: EventHandler):
        for widget in self:
            widget.events(event_handler)

    def render(self, display: pygame.Surface):
        for widget in self:
            widget.render(display)


class WidgetCarrier(WidgetGroup, Widget):

    def __init__(
            self,
            gui: Gui,
            dim: RectangleArrayType,
            color: Tuple,
            active: bool = True,
            layer: int = 1,
    ):
        Widget.__init__(self, None, dim)
        WidgetGroup.__init__(self, gui, active=active, layer=layer)
        self._color = color

    def add_widget(self, widget: Widget):
        widget.snap(anchor=self.topleft)
        super().add_widget(widget)

    def render(self, display: pygame.Surface):
        pygame.draw.rect(display, self._color, self)
        super().render(display)