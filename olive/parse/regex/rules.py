from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Generic, Optional, TypeVar, Self

"""
Rule Options
"""


@dataclass
class RuleOptions(object):
    inclusive: tuple[bool, bool] = (True, True)
    cache: bool = False

    @classmethod
    def parse(cls, symbol: str) -> tuple[str, Self]:
        def parse_inclusive(value: str) -> tuple[bool, bool]:
            return value[0] == "1", value[1] == "1"

        def parse_cache(value: str) -> bool:
            return value == "1"

        if "(" not in symbol:
            return symbol, cls()

        symbol, options_raw = symbol.split("(")
        options_raw_list = options_raw[:-1].split(",")

        # Defaults
        inclusive = (True, True)
        cache = True

        for option_raw in options_raw_list:
            name, value = [v.strip() for v in option_raw.split("=")]
            match name:
                case "inclusive":
                    inclusive = parse_inclusive(value)
                case "cache":
                    cache = parse_cache(value)

        return symbol, cls(inclusive, cache)


T = TypeVar("T")


@dataclass
class Rule(ABC, Generic[T]):
    symbol: T
    rule: list[T]
    options: RuleOptions

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
    symbol, options = RuleOptions.parse(symbol)

    if not symbol or not rule:
        return None

    if symbol == "SPECIAL-RULE":
        rs = rule.split(" ")
        assert len(rs) > 0
        return SpecialRule(rs[0], [] if len(rs) == 1 else rs[1:], options)
    else:
        return RawRule(symbol, rule.split(" "), options)


def load_rules(path: Path) -> list[RawRule | SpecialRule]:
    rules = []
    with open(path, "r") as infile:
        for line in infile.readlines():
            parsed_rule = parse_rule_from_str(line)
            if parsed_rule is not None:
                rules.append(parsed_rule)

    return rules
