from typing import Tuple, Union

import pygame
from enum import Enum

from engine.tools import Align, Vector
from engine.gui.gui import Gui, Register, Widget, WidgetGroup, CoordinateArrayType, RectangleArrayType, WidgetCarrier
from engine.events import EventHandler


class TextWidget(Widget):
    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            text: int = None,
            text_size: int = None,
            bold: bool = True,
            **kwargs,
    ):
        super().__init__(group, (*pos, 0, 0), **kwargs)
        self._text_register = Register(text)
        self.color = color
        self.text_size = self._gui.text_size if text_size is None else text_size
        self.bold = bold
        self.update_dim(text)

    def render_text(
            self,
            display: pygame.Surface,
            text: str,
            color: Tuple,
            pos: CoordinateArrayType = None,
            align: str = None
    ):
        if align is None:
            align = self._align
        if pos is None:
            pos = getattr(self, self._align)

        surface = self.font.render(text, True, color)
        rect = surface.get_rect()

        setattr(rect, align, pos)
        display.blit(surface, rect)
        return rect.width, rect.height

    def update_dim(self, text: str):
        width, height = self.font.size(text)
        self.update(self.left, self.top, width, height)
        self.snap()

    @property
    def font(self) -> pygame.font.Font:
        return self._gui.FONT[self.bold][self.text_size]

    @property
    def text(self): return str(self._text_register.value)


class TextLabel(TextWidget):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            text: str = "",
            register: str = None,
            **kwargs,
    ):
        super().__init__(group, pos, color, text, **kwargs)
        if register is not None:
            self._text_register = self._gui.register(register, text)
            self.update_dim(str(self._text_register))

    def render(self, display: pygame.Surface):
        self.render_text(display, str(self._text_register), self.color)


class DataLabel(TextWidget):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            text: str,
            value: float = 0.0,
            decimals: int = 2,
            register: str = None,
            **kwargs,
    ):
        super().__init__(group, pos, color, f"{text}: ", **kwargs)
        self._value_register = self._gui.register(register, value)
        self._decimals = decimals

    def render(self, display: pygame.Surface):
        w1, h1 = self.font.size(self.text)
        w2, h2 = self.font.size(str(self._value_register))
        self.update(self.left, self.top, w1 + w2, max(h1, h2))
        self.snap()

        self.render_text(display, self.text, self.color[0], self.midleft + Vector(w1 / 2, 0), Align.C)
        self.render_text(display, str(self._value_register), self.color[1], self.midleft + Vector(w1 + w2 / 2, 0), Align.C)

    @property
    def value(self) -> float:
        return self._value_register.value

    @value.setter
    def value(self, new_value: Union[float, int, str]):
        new_value = float(new_value) if isinstance(new_value, str) else new_value
        self._value_register.value = round(float(new_value), self._decimals)


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
            initial_value: float = 0.0,
            register: str = None,
            **kwargs,
    ):
        super().__init__(group, self.dim(pos, length), **kwargs)

        self.hold = False
        self.moved = False

        self._value_register = self._gui.register(register, initial_value)

        self._rail: Optional[pygame.Rect] = None
        self._slider: Optional[pygame.Rect] = None
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
        if slide != self._value_register.value and self.hold:
            self._value_register.value = slide
            self.moved = True

        self._slider.left = min(max(self._value_register.value, 0), self.width) + self.left - self.height / 2

    @property
    def value(self) -> float:
        return self._value_register.value / self.width

    @value.setter
    def value(self, val: float):
        self._value_register.value = min(max(val * self.width, 0), self.width)


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
        if slide != self._value_register.value and self.hold:
            self._value_register.value = slide
            self.moved = True
        self._slider.top = min(max(self._value_register.value, 0), self.height) + self.top - self.width / 2

    @property
    def value(self) -> float:
        return self._value_register.value / self.height

    @value.setter
    def value(self, val: float):
        self._value_register.value = min(max(val * self.height, 0), self.height)


class Switch(TextWidget):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            colors: Tuple,
            text: str,
            active: bool = False,
            register: str = None,
            **kwargs,
    ):
        super().__init__(group, pos, colors, text, **kwargs)
        self._switch_register = self._gui.register(register, active)

        self.last_active = active
        self.activated = False
        self.deactivated = False

    def relay(self, active: bool = None):
        self._switch_register.value = not self._switch_register.value if active is None else active

    def events(self, event_handler: EventHandler):
        super().events(event_handler)

        self.activated = self.active and not self.last_active
        self.deactivated = self.last_active and not self.active
        self.last_active = self.active

    @property
    def active(self) -> bool: return self._switch_register.value


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
            register: str = None,
            **kwargs,
    ):
        super().__init__(group, pos, color, f"{text}: ", active=False, register=None, **kwargs)

        self._value_register = self._gui.register(register, value)
        self._visible_value = self._value_register.value
        self._minimum_content_width = self.font.size(str(self._visible_value))[0] + self.font.size(self.text)[0]

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
                self._visible_value = self._value_register.value
                self.deactivate()
            else:
                self.type(key)
        else:
            self._visible_value = self._value_register.value

    def activate(self):
        self._visible_value = ""
        self._switch_register.value = True
        self._gui.focus_widget(self)

    def deactivate(self):
        if self._visible_value:
            self.value = self._visible_value
        self._switch_register.value = False
        self._gui.release_widget(self)

    def type(self, char: str):
        self._visible_value = self._visible_value + char

    @property
    def value(self) -> Union[float, str]:
        return self._visible_value if self.active else self._value_register.value

    @value.setter
    def value(self, new_value: Union[float, str]):
        self._value_register.value = str(new_value)
        self._visible_value = self._value_register.value

    def render(self, display: pygame.Surface):
        color = self.color[self.hovered or self.active]
        value = self._visible_value if self.active else self._value_register.value
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
        return float(self._value_register)

    @value.setter
    def value(self, new_value: Union[float, int, str]):
        if new_value == "":
            self._value_register.value = 0.0
        if self.is_numeric(new_value):
            self._value_register.value = self.format(new_value)
        self._visible_value = self._value_register.value


class Dropdown(Switch):

    def __init__(
            self,
            group: WidgetGroup,
            pos: CoordinateArrayType,
            color: Tuple,
            items: set,
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