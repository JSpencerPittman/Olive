from enum import Enum
from typing import Literal, Optional, overload
from pathlib import Path

from olive.parse.regex.rules import QuantizedRule, RawRule


class SpecialSymbols(Enum):
    LEFT_PAREN = (0, "(")
    RIGHT_PAREN = (1, ")")

    @staticmethod
    def from_symbol(symbol: str | int) -> Optional["SpecialSymbols"]:
        comp_idx = 1 if isinstance(symbol, str) else 0
        for ss in SpecialSymbols:
            if ss.value[comp_idx] == symbol:
                return ss
        return None

    @staticmethod
    def count() -> int:
        return len(SpecialSymbols)

    @staticmethod
    def is_special_symbol(symbol: str | int) -> bool:
        return SpecialSymbols.from_symbol(symbol) is not None

    def __eq__(self, value):
        if isinstance(value, SpecialSymbols):
            return super().__eq__(value)
        elif isinstance(value, str) or isinstance(value, int):
            v = SpecialSymbols.from_symbol(value)
            if v is None:
                return False
            return super().__eq__(v)
        else:
            assert False


class Language(object):
    def __init__(self):
        self._quantized_symbols = {}

    @property
    def num_symbols(self) -> int:
        return len(self._quantized_symbols) + SpecialSymbols.count()

    @overload
    def quantize_symbol(
        self, symbol: str, immutable: Literal[False] = False
    ) -> int: ...

    @overload
    def quantize_symbol(
        self, symbol: str, immutable: Literal[True] = True
    ) -> Optional[int]: ...

    def quantize_symbol(self, symbol: str, immutable: bool = False) -> Optional[int]:
        if ss := SpecialSymbols.from_symbol(symbol):
            return ss.value[0]
        if symbol not in self._quantized_symbols:
            if not immutable:
                self._quantized_symbols[symbol] = self.num_symbols
            else:
                return None

        return self._quantized_symbols[symbol]

    def quantize_rule(self, rule: RawRule):
        return QuantizedRule(
            self.quantize_symbol(rule.symbol),
            [self.quantize_symbol(symbol) for symbol in rule.rule],
        )


if __name__ == "__main__":
    rules_path = Path(__file__).parent / "rules.txt"
    raw_rules = RawRule.load(rules_path)
    language = Language()
    quantized = [language.quantize_rule(rule) for rule in raw_rules]
    print(quantized)
