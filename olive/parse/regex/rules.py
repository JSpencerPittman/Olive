from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Rule(ABC, Generic[T]):
    symbol: T
    rule: list[T]

    @abstractmethod
    def __repr__(self) -> str: ...


@dataclass
class RawRule(Rule[str]):
    symbol: str
    rule: list[str]

    @classmethod
    def load(cls, path: Path) -> list["RawRule"]:
        def parse_rule(line: str) -> Optional[RawRule]:
            parts = line.split(":=")
            if len(parts) != 2:
                return None
            symbol, rule = parts[0].strip(), parts[1].strip()
            if not symbol or not rule:
                return None

            return cls(symbol, rule.split(" "))

        rules = []
        with open(path, "r") as infile:
            for line in infile.readlines():
                parsed_rule = parse_rule(line)
                if parsed_rule is not None:
                    rules.append(parsed_rule)

        return rules

    def __repr__(self) -> str:
        return f"{self.symbol} := {self.rule}"


@dataclass
class QuantizedRule(Rule[int]):
    symbol: int
    rule: list[int]

    def __repr__(self) -> str:
        return f"{self.symbol} := {self.rule}"


if __name__ == "__main__":
    rules_path = Path(__file__).parent / "rules.txt"
    print(RawRule.load(rules_path))
