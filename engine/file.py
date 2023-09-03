import json
from configparser import ConfigParser

from abc import ABC, abstractmethod
from typing import Any


class File(ABC):
    _EXTENSION = ""

    def __init__(self, path: str = None, read_only: bool = True):
        self._file = None if path is None else f"{path}.{self._EXTENSION}"
        self._data = {}
        self._read_only = read_only
        self.load()

    def __iter__(self) -> tuple:
        yield from self._data.items()

    def __str__(self) -> str:
        return self._file

    @property
    def data(self) -> dict:
        return self._data

    def load(self):
        self._load()

    def save(self):
        if self._read_only:
            print(f"WARNING: {self._file} is read only!")
        else:
            self._save()

    @abstractmethod
    def _save(self) -> None:
        pass

    @abstractmethod
    def _load(self) -> None:
        pass


class JsonFile(File):
    _EXTENSION = "json"

    def _load(self):
        with open(self._file, "r") as FILE:
            self._data = json.load(FILE)

            for key, value in self.data.items():
                if not key.startswith("_"):
                    setattr(self, key, value)

    def _save(self):
        for key in self._data:
            self._data[key] = getattr(self, key)

        with open(self._file, "w") as FILE:
            json.dump(self._data, FILE, indent=2, sort_keys=False)

    @property
    def data(self) -> dict:
        return self._data


class DynamicJsonFile(JsonFile):

    def __init__(self, path: str):
        super().__init__(path, read_only=False)

    @property
    def data(self) -> dict:
        return self._substitute_values(self._data)

    def _substitute_values(self, data: dict) -> Any:
        if isinstance(data, dict):
            return {key: self._substitute_values(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._substitute_values(element) for element in data]
        elif isinstance(data, str):
            if data in self._data.keys():
                return self._data[data]
            else:
                for key in self._data.keys():
                    data = data.replace(key, str(self._data[key]))

                if any(char in data for char in "+-*/"):
                    return eval(data)
                else:
                    return data
        else:
            return data


class IniFile(File):
    _EXTENSION = "ini"
    _FLOATING_POINT_CHARACTER = '.'

    def __init__(self, path: str = None, read_only: bool = True):
        self._config = ConfigParser()
        self._config.optionxform = str

        super().__init__(path, read_only)

    def _load(self) -> None:
        self._config.read(self._file)
        self._data = {section: self._config[section] for section in self._config.sections()}

        for section in self._data.values():
            for name, value in section.items():
                if value.replace(IniFile._FLOATING_POINT_CHARACTER, '').isnumeric():
                    value = float(value) if '.' in value else int(value)
                elif value.lower() in ("true", "false"):
                    value = value == "true"
                setattr(self, name.upper(), value)

    def _save(self) -> None:
        for section_name, section in self._data.items():
            for name in section.keys():
                self._config.set(section_name, name, str(getattr(self, name.upper())))

        with open(self._file, "w") as FILE:
            self._config.write(FILE)
