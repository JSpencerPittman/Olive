from typing import ClassVar, Type
from dataclasses import dataclass
from abc import ABC


@dataclass
class Fruit(ABC):
    CLASS_NAME: ClassVar[str] = "Fruit"
    name: str

    @classmethod
    def is_me(cls, s: str) -> bool:
        return s == cls.CLASS_NAME


@dataclass
class Apple(Fruit):
    CLASS_NAME: ClassVar[str] = "Apple"
    name: str


CLASSES: list[Type[Fruit]] = [Fruit, Apple]

for c in CLASSES:
    print(c.CLASS_NAME)
