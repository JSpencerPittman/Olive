from enum import Enum
from typing import Literal, Optional, overload
from pathlib import Path

from olive.parse.regex.rules import QuantizedRule, RawRule


class SpecialSymbols(Enum):
    LEFT_PAREN = (0, "(")
    RIGHT_PAREN = (1, ")")

    @staticmethod
    def from_symbol(s: str) -> Optional["SpecialSymbols"]:
        for symbol in SpecialSymbols:
            if symbol.value[1] == s:
                return symbol
        return None

    @staticmethod
    def count() -> int:
        return len(SpecialSymbols)


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
