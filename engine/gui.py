from abc import ABC, abstractmethod
from enum import Enum
from math import floor
from typing import Optional, Union, Tuple, List, Iterator

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

    @property
    def text_size(self):
        return min(Gui.FONT_SIZES, key=lambda element: abs(element - self._text_size))

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


# === [ INHERITED WIDGET CLASSES ] =================================================================================== #


class TextLabel(Widget):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            text: str,
            text_size: int = None,
            bold: bool = True,
            anchor: CoordinateArrayType = None,
            align: str = Align.TL,
            layer: int = 1,
            **kwargs,
    ):
        super().__init__(group, (*pos, 0, 0), anchor, align, layer, **kwargs)
        self.align = align
        self.color = color
        self.text_size = self._gui.text_size if text_size is None else text_size
        self.bold = bold
        self.text = None

        if text is not None:
            self.update_text(text)

    def update_text(self, text: str):
        self.text = text
        width, height = self.font.size(text)
        self.update(self.left, self.top, width, height)
        self.snap()

    def render_text(
            self,
            display: pygame.Surface,
            text: str,
            color: Tuple,
            pos: CoordinateArrayType = None,
            align: str = None
    ):
        if align is None:
            align = self.align
        if pos is None:
            pos = getattr(self, self.align)

        surface = self.font.render(text, True, color)
        rect = surface.get_rect()

        setattr(rect, align, pos)
        display.blit(surface, rect)
        return rect.width, rect.height

    def render(self, display: pygame.Surface):
        self.render_text(display, self.text, self.color)

    @property
    def font(self) -> pygame.font.Font:
        return self._gui.FONT[self.bold][self.text_size]


class DataLabel(TextLabel):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            text: str,
            value: float = 0.0,
            decimals: int = 2,
            **kwargs,
    ):
        super().__init__(group, pos, color, f"{text}: ", **kwargs)
        self._value = value
        self._decimals = decimals

    def render(self, display: pygame.Surface):
        w1, h1 = self.font.size(self.text)
        w2, h2 = self.font.size(str(self._value))
        self.update(self.left, self.top, w1 + w2, max(h1, h2))
        self.snap()

        self.render_text(display, self.text, self.color[0], self.midleft + Vector(w1 / 2, 0), Align.C)
        self.render_text(display, str(self._value), self.color[1], self.midleft + Vector(w1 + w2 / 2, 0), Align.C)

    @property
    def value(self) -> float:
        return self._value

    @value.setter
    def value(self, new_value: Union[float, int, str]):
        new_value = float(new_value) if isinstance(new_value, str) else new_value
        self._value = round(float(new_value), self._decimals)


class Button(TextLabel):

    def render(self, display: pygame.Surface):
        self.render_text(display, self.text, self.color[self.hovered])


class Slider(Widget):
    SIZE = 20
    RAIL = 5

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            length: int,
            initial_value=0.0,
            **kwargs,
    ):
        super().__init__(group, self.dim(pos, length), **kwargs)

        self.hold = False
        self.moved = False

        self._rail: Optional[pygame.Rect] = None
        self._slider: Optional[pygame.Rect] = None
        self._slide = 0
        self._color = color
        self._initial_value = initial_value

    def events(self, event_handler: EventHandler):
        super().events(event_handler)

        if self.hovered:
            if event_handler.mouse[0, "press"]:
                self.hold = True
            elif event_handler.mouse[2, "press"]:
                self.value = self._initial_value
            elif scroll := event_handler.mouse["scroll"]:
                self.value = self.value + scroll * 0.005
        if not event_handler.mouse[0, "hold"]:
            self.hold = False

    def render(self, display: pygame.Surface):
        color = self._color[self.hovered or self.hold]
        pygame.draw.rect(display, color[1], self._rail)
        pygame.draw.rect(display, color[0], self._slider)

    @staticmethod
    def dim(pos, length) -> RectangleArrayType:
        pass

    @property
    def value(self) -> float: return 0.0

    @value.setter
    def value(self, value): pass


class HorizontalSlider(Slider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rail = pygame.Rect(self.left, int((self.height - Slider.RAIL) / 2) + self.top, self.width, Slider.RAIL)
        self._slider = pygame.Rect(self.left, self.top, Slider.SIZE, Slider.SIZE)
        self.value = self._initial_value

    @staticmethod
    def dim(pos, length) -> RectangleArrayType:
        return *pos, length, Slider.SIZE

    def events(self, event_handler: EventHandler):
        super().events(event_handler)

        slide = min(max(event_handler.mouse.pos.x - self.left, 0), self.width)
        if slide != self._slide and self.hold:
            self._slide = slide
            self.moved = True

        self._slider.left = self._slide + self.left - self.height / 2

    @property
    def value(self) -> float:
        return self._slide / self.width

    @value.setter
    def value(self, val: float):
        slide = val * self.width
        self._slide = min(max(slide, 0), self.width)
        self._slider.left = self._slide + self.left - self.height / 2


class VerticalSlider(Slider):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rail = pygame.Rect(int((self.width - Slider.RAIL) / 2) + self.left, self.top, Slider.RAIL, self.height)
        self._slider = pygame.Rect(self.left, self.top, Slider.SIZE, Slider.SIZE)
        self.value = self._initial_value

    @staticmethod
    def dim(pos, length) -> RectangleArrayType:
        return *pos, Slider.SIZE, length

    def events(self, event_handler: EventHandler):
        super().events(event_handler)

        slide = min(max(event_handler.mouse.pos.y - self.top, 0), self.height)
        if slide != self._slide and self.hold:
            self._slide = slide
            self.moved = True

        self._slider.top = self._slide + self.top - self.width / 2

    @property
    def value(self) -> float:
        return self._slide / self.height

    @value.setter
    def value(self, val: float):
        slide = val * self.height
        self._slide = min(max(slide, 0), self.height)
        self._slider.top = self._slide + self.top - self.width / 2


class Switch(TextLabel):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            colors: Tuple,
            text: str,
            active: bool = False,
            **kwargs,
    ):
        super().__init__(group, pos, colors, text, **kwargs)
        self.active = active
        self.last_active = active
        self.activated = False
        self.deactivated = False

    def relay(self):
        self.active = not self.active

    def events(self, event_handler: EventHandler):
        super().events(event_handler)

        self.activated = self.active and not self.last_active
        self.deactivated = self.last_active and not self.active
        self.last_active = self.active


class FlipSwitch(Switch):
    STATE_TEXT = ("OFF", "ON")

    def events(self, event_handler: EventHandler):
        super().events(event_handler)
        if self.pressed:
            self.relay()

    def render(self, display: pygame.Surface):
        color = self.color[self.hovered]
        w1, h1 = self.font.size(self.text)
        w2, h2 = self.font.size(FlipSwitch.STATE_TEXT[self.active])
        self.update(self.left, self.top, w1 + w2, max(h1, h2))
        self.snap()

        self.render_text(display, self.text, color[0], self.midleft + Vector(w1 / 2, 0), Align.C)
        self.render_text(display, FlipSwitch.STATE_TEXT[self.active], color[1],
                         self.midleft + self.midleft + Vector(w1 + w2 / 2, 0), Align.C)


class TextInput(Switch):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            text: str,
            value: str = None,
            **kwargs,
    ):
        super().__init__(group, pos, color, f"{text}: ", active=False, **kwargs)

        self._value = "" if value is None else str(value)
        self._visible_value = self._value
        self._minimum_content_width = self.font.size(str(value))[0] + self.font.size(self.text)[0]

    def events(self, event_handler: EventHandler):
        super().events(event_handler)

        if event_handler.mouse[0, "press"]:
            if self.hovered and not self.active:
                self.activate()
            else:
                self.deactivate()

        if self.active:
            key = event_handler["type"]
            if key == "BACKSPACE":
                self._visible_value = self._visible_value[:-1]
            elif key == "RETURN":
                self.deactivate()
            elif key == "ESCAPE":
                self._visible_value = self._value
                self.deactivate()
            else:
                self.type(key)

    def activate(self):
        self._visible_value = ""
        self.active = True
        self._gui.focus_widget(self)

    def deactivate(self):
        if self._visible_value:
            self.value = self._visible_value
        self.active = False
        self._gui.release_widget(self)

    def type(self, char: str):
        self._visible_value = self._visible_value + char

    @property
    def value(self) -> Union[float, str]:
        return self._visible_value if self.active else self._value

    @value.setter
    def value(self, new_value: Union[float, str]):
        self._value = str(new_value)
        self._visible_value = self._value

    def render(self, display: pygame.Surface):
        color = self.color[self.hovered or self.active]
        value = self._visible_value if self.active else self.value
        w1, h1 = self.font.size(self.text)
        w2, h2 = self.font.size(str(value))
        self.update(self.left, self.top, max(w1 + w2, self._minimum_content_width), max(h1, h2))
        self.snap()

        self.render_text(display, self.text, color[0], self.midleft + Vector(w1 / 2, 0), Align.C)
        self.render_text(display, str(value), color[1], self.midleft + Vector(w1 + w2 / 2, 0), Align.C)


class NumericInput(TextInput):
    NUMERIC = (".", "-", "+")

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            text: str,
            value: float = 0.0,
            limits: Tuple[float] = (None, None),
            increment: float = 1,
            decimals: int = 2,
            **kwargs,
    ):
        super().__init__(group, pos, color, text, **kwargs)
        self._limits = limits
        self._increment = increment
        self._decimals = decimals
        self.value = value

    def events(self, event_handler: EventHandler):
        super().events(event_handler)
        if not self.active and self.hovered:
            self.value = self.value + event_handler.mouse["scroll"] * self._increment

    @staticmethod
    def is_numeric(value: str) -> bool:
        value = str(value)
        if value.startswith("-") or value.startswith("+"):
            value = value[1:]
        return value.replace(".", "").isnumeric()

    def format(self, value: str) -> float:
        if self._limits[0] is not None:
            value = max(self._limits[0], float(value))
        if self._limits[1] is not None:
            value = min(self._limits[1], float(value))
        return round(float(value), self._decimals)

    def type(self, char: str):
        if char.isnumeric() or char in NumericInput.NUMERIC:
            super().type(char)

    @property
    def value(self) -> float:
        return float(self._value)

    @value.setter
    def value(self, new_value: Union[float, int, str]):
        if new_value == "":
            self.value = "0.0"
        if self.is_numeric(new_value):
            self._value = self.format(new_value)
        self._visible_value = self._value


class Dropdown(Switch):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            items,
            text: str = None,
            initial: Enum = None,
            **kwargs,
    ):
        super().__init__(group, pos, color, f"{text}: ", active=False, **kwargs)
        self._items = items
        self._order = items
        self.select(initial)
        self._hovered_index = 0
        self._length = len(items)

    @property
    def layer(self) -> int:
        return -1 if self.active else self._layer

    def select(self, selected: Enum):
        self._order = sorted(self._items.names(), key=lambda item: int(item != selected))

    @property
    def selected(self) -> Enum:
        return self._items[self._order[0]]

    def step(self, direction: int = 0):
        self._hovered_index += direction
        if self._hovered_index < 0:
            self._hovered_index = len(self._items) - 1
        if self._hovered_index >= len(self._items):
            self._hovered_index = 0

    def events(self, event_handler: EventHandler):
        super().events(event_handler)

        if self.pressed:
            if self.active:
                self.active = False
                self.select(self._order[self._hovered_index])
                self._hovered_index = 0
            else:
                self.active = True

        if self.hovered:
            if self.active:
                pos = event_handler.mouse.pos.y - self.top
                self._hovered_index = floor(pos * self._length / self.height) if self.active else 0
            else:
                if step := event_handler.mouse["scroll"]:
                    self.step(step)
                    self.select(self._items.names()[self._hovered_index])
        else:
            self.active = False

        if self.activated:
            self._gui.focus_widget(self, overwrite=True)
        if self.deactivated:
            self._gui.release_widget(self)

    def render(self, display: pygame.Surface):

        color = self.color[self.hovered or self.active][0]
        width, _ = self.render_text(display, self.text, color, align=Align.TL)
        height = 0
        stretch = 0

        if self.active:
            x, y, w, h = self
            tw, _ = self.font.size(self.text)
            pygame.draw.rect(display, self.color[0], (x + tw, y, w - tw, h))

        for index, item in enumerate(self._order):
            glow = index == self._hovered_index and self.active or not self.active and self.hovered
            color = self.color[glow][1]
            pos = self.topleft + Vector(width, (self.text_size + 5) * index)
            w, _ = self.render_text(display, item, color, pos, Align.TL)
            height = height + self.text_size + 5
            stretch = max(stretch, w)

            if not self.active:
                break

        self.update(self.left, self.top, width + stretch, height)
        self.snap()


class FloatingWindow(WidgetCarrier):

    HEADER = 40
    GAP = 8

    def __init__(
            self,
            gui: Gui,
            dim: RectangleArrayType,
            color: Tuple,
            title: str = "",
            active: bool = False,
            layer: int = 1,
    ):
        x, y, w, h = dim
        super().__init__(gui, (x, y, w, h + FloatingWindow.HEADER), color, active=active, layer=layer)
        self._header = pygame.Rect(x, y - FloatingWindow.HEADER, w, FloatingWindow.HEADER)
        side = FloatingWindow.HEADER - FloatingWindow.GAP * 2
        self._close = pygame.Rect(0, 0, side, side)
        self._close.topright = self._header.topright + Vector(-FloatingWindow.GAP, FloatingWindow.GAP)
        self._float = Vector(0, 0)

        pos = Vector(FloatingWindow.GAP, FloatingWindow.GAP - FloatingWindow.HEADER)
        self._title = TextLabel(self, pos, self._color[2], title)

        self.header_hovered = False
        self.header_pressed = False
        self.header_holded = False
        self.close_hovered = False
        self.close_pressed = False

    @property
    def layer(self):
        return -1 if self._gui.is_focused(self) else self._layer

    def float(self, vector: Vector):
        self.topleft = self._base - vector
        self._header.bottomleft = self.topleft
        self._close.topright = self._header.topright + Vector(-FloatingWindow.GAP, FloatingWindow.GAP)
        for widget in self._widgets:
            widget.snap(anchor=self.topleft)

    def events(self, event_handler: EventHandler):
        WidgetGroup.events(self, event_handler)
        Widget.events(self, event_handler)

        mouseclick = event_handler.mouse[0, "press"]

        self.close_hovered = event_handler.mouse.focused(self._close)
        self.header_hovered = event_handler.mouse.focused(self._header)

        self.close_pressed = self.close_hovered and mouseclick
        self.header_pressed = self.header_hovered and mouseclick

        self.pressed = self.pressed or self.header_pressed
        self.pressed_elsewhere = not self.pressed and mouseclick

        if self.close_pressed:
            self._gui.release_widget(self)
            self._gui.deactivate_group(self)

        if self.header_pressed:
            self.header_holded = True
        if not event_handler.mouse[0, "hold"]:
            self.header_holded = False

        if self.header_holded:
            self.float(event_handler.mouse.drag)
        else:
            self.snap(self.topleft)

        if self.pressed:
            self._gui.focus_widget(self, overwrite=True)
        if self.pressed_elsewhere:
            self._gui.release_widget(self, event_handler)

    def render(self, display: pygame.Surface):
        gap = FloatingWindow.GAP
        rect = pygame.Rect(self.left + gap, self.top, self.width - gap * 2, self.height - gap)
        pygame.draw.rect(display, self._color[1][self._gui.is_focused(self)], self)
        pygame.draw.rect(display, self._color[0], rect)
        pygame.draw.rect(display, self._color[1][self._gui.is_focused(self)], self._header)
        pygame.draw.rect(display, self._color[3][self.close_hovered], self._close)
        WidgetGroup.render(self, display)
