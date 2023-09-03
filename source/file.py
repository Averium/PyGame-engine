import json
from abc import ABC, abstractmethod
from os.path import basename
from typing import Tuple, Union, Any, Optional

import mat4py
from numpy import array as matrix
from openpyxl import load_workbook, Workbook


class File(ABC):
    EXTENSION = ""

    def __init__(self, path: str = None, read_only: bool = True):
        self._file = None if path is None else f"{path}.{self.EXTENSION}"
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
    EXTENSION = "json"

    def _load(self):
        with open(self._file, "r") as FILE:
            self._data = json.load(FILE)

            for key, value in self.data.items():
                if not key.startswith("_"):
                    setattr(self, key, value)

    def _save(self):
        with open(self._file, "w") as FILE:
            for key in self._data:
                self._data[key] = getattr(self, key)
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


class MatFile(File):
    EXTENSION = "mat"
    Y_AXIS = "Y"
    X_AXIS = "X"
    NAME_FIELD = "Name"
    DATA_FIELD = "Data"

    def __init__(self, path: str):
        self._main_field = basename(path)
        super().__init__(path, True)

    def __str__(self) -> str:
        return "\n".join(name for name in self._data[self._main_field]["Y"]["Name"])

    def _load(self):
        self._data = mat4py.loadmat(self._file)
        names = self._data[self._main_field][MatFile.Y_AXIS][MatFile.NAME_FIELD]
        arrays = self._data[self._main_field][MatFile.Y_AXIS][MatFile.DATA_FIELD]
        for name, array in zip(names, arrays):
            name = name.replace(".", "_")
            name = name.replace("[", "_")
            name = name.replace("]", "_")
            name = name.replace("][", "_")
            setattr(self, name, matrix(array))

    def _save(self): pass


class ExcelFile(File):
    EXTENSION = "xlsx"

    def __init__(self, filename: str):
        self._data: Optional[Workbook] = None
        super().__init__(filename, True)

    def __getitem__(self, sheet_cells: Tuple[str, str]) -> Union[int, float, str]:
        sheet, cells = sheet_cells
        return self._data[sheet][cells]

    def _load(self):
        self._data = load_workbook(self._file, read_only=self._read_only)

    def _save(self): pass
