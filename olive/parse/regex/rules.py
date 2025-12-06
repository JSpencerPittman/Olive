from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass
class Rule(ABC, Generic[T]):
    symbol: T
    rule: list[T]
    inclusive: tuple[bool, bool] = (True, True)

    @abstractmethod
    def __repr__(self) -> str: ...


@dataclass
class SpecialRule(Rule[str]):
    symbol: str
    rule: list[str]

    def __repr__(self) -> str:
        return f"{self.symbol} := {self.rule}"


@dataclass
class RawRule(Rule[str]):
    symbol: str
    rule: list[str]

    def __repr__(self) -> str:
        return f"{self.symbol} := {self.rule}"


@dataclass
class QuantizedRule(Rule[int]):
    symbol: int
    rule: list[int]

    def __repr__(self) -> str:
        return f"{self.symbol} := {self.rule}"


def parse_rule_from_str(line: str) -> Optional[RawRule | SpecialRule]:
    parts = line.split(":=")
    if len(parts) != 2:
        return None
    symbol, rule = parts[0].strip(), parts[1].strip()

    inclusivity = (True, True)
    if "(" in symbol:
        symbol, inc_raw = symbol.split("(")
        symbol = symbol.split("(")[0]
        inclusivity = inc_raw[0] == "1", inc_raw[1] == "1"

    if not symbol or not rule:
        return None

    if symbol == "SPECIAL-RULE":
        rs = rule.split(" ")
        assert len(rs) > 0
        return SpecialRule(rs[0], [] if len(rs) == 1 else rs[1:])
    else:
        return RawRule(symbol, rule.split(" "), inclusivity)


def load_rules(path: Path) -> list[RawRule | SpecialRule]:
    rules = []
    with open(path, "r") as infile:
        for line in infile.readlines():
            parsed_rule = parse_rule_from_str(line)
            if parsed_rule is not None:
                rules.append(parsed_rule)

    return rules
