from abc import ABC, abstractmethod
from typing import Union


class GameState(ABC):

    def __init__(self, name: str, state_machine: "StateMachine"):
        self.name = name
        self.state_machine: StateMachine = state_machine

    @abstractmethod
    def check_conditions(self) -> Union[str, None]:
        pass

    def entry_actions(self):
        pass

    def exit_actions(self):
        pass

    def events(self, *args, **kwargs) -> None:
        pass

    def logic(self, *args, **kwargs) -> None:
        pass

    def render(self, *args, **kwargs) -> None:
        pass


class StateMachine(ABC):

    def __init__(self, initial: GameState):
        self.initial: str = initial.name
        self._states: dict = {}

        self.add_state(initial)

        self._active: GameState = initial
        self._last: GameState = initial

        initial.entry_actions()

    def add_state(self, *states: GameState):
        for state in states:
            self._states[state.name] = state

    @property
    def current_state(self) -> str:
        return self._active.name

    @property
    def last_state(self) -> str:
        return self._last.name

    @current_state.setter
    def current_state(self, name: str):
        self._active.exit_actions()
        self._last = self._active
        self._active = self._states[name]
        self._active.entry_actions()

    def update_states(self):
        if (new_state := self._active.check_conditions()) is not None:
            self.current_state = new_state

    def state_events(self, *args, **kwargs):
        self._active.events(*args, **kwargs)

    def state_logic(self, *args, **kwargs):
        self._active.logic(*args, **kwargs)

    def state_render(self, *args, **kwargs):
        self._active.render(*args, **kwargs)
