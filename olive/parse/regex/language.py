from enum import Enum
from typing import Literal, Optional, overload
from pathlib import Path

from olive.parse.regex.rules import QuantizedRule, RawRule


class SpecialSymbols(Enum):
    LEFT_PAREN = (0, "(", "left_paren")
    RIGHT_PAREN = (1, ")", "right_paren")
    ASTERISK = (2, "*", "asterisk")
    QUESTION_MARK = (3, "?", "question_mark")
    PLUS_SIGN = (4, "+", "plus_sign")
    PIPE = (5, "|", "pipe")

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

    @staticmethod
    def literal_from_escape(escape: str):
        if not escape.startswith("<:") or not escape.endswith(":>"):
            return None
        for symbol in SpecialSymbols:
            if f"<:{symbol.value[2]}:>" == escape:
                return symbol.value[1]
        return None

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
        self,
        symbol: str,
        treat_special_symbols: bool = True,
        immutable: Literal[False] = False,
    ) -> int: ...

    @overload
    def quantize_symbol(
        self,
        symbol: str,
        treat_special_symbols: bool = True,
        immutable: Literal[True] = True,
    ) -> Optional[int]: ...

    def quantize_symbol(
        self, symbol: str, treat_special_symbols: bool = False, immutable: bool = False
    ) -> Optional[int]:
        if treat_special_symbols and (ss := SpecialSymbols.from_symbol(symbol)):
            return ss.value[0]
        if se := SpecialSymbols.literal_from_escape(symbol):
            symbol = se
        if symbol not in self._quantized_symbols:
            if not immutable:
                self._quantized_symbols[symbol] = self.num_symbols
            else:
                return None

        return self._quantized_symbols[symbol]

    def quantize_rule(self, rule: RawRule):
        return QuantizedRule(
            self.quantize_symbol(rule.symbol, treat_special_symbols=True),
            [
                self.quantize_symbol(symbol, treat_special_symbols=True)
                for symbol in rule.rule
            ],
        )

    def dequantize_symbol(self, quantized: int) -> Optional[str]:
        if quantized >= self.num_symbols:
            return None
        for s, qt in self._quantized_symbols.items():
            if qt == quantized:
                return s
        assert False


if __name__ == "__main__":
    rules_path = Path(__file__).parent / "rules.txt"
    raw_rules = RawRule.load(rules_path)
    language = Language()
    quantized = [language.quantize_rule(rule) for rule in raw_rules]
    print(quantized)
