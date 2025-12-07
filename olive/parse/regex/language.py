from enum import Enum
from typing import Optional

from olive.parse.regex.rules import QuantizedRule, RawRule


class SpecialSymbols(Enum):
    LEFT_PAREN = (0, "(", "left_paren")
    RIGHT_PAREN = (1, ")", "right_paren")
    ASTERISK = (2, "*", "asterisk")
    QUESTION_MARK = (3, "?", "question_mark")
    PLUS_SIGN = (4, "+", "plus_sign")
    PIPE = (5, "|", "pipe")
    DOT = (6, ".", "dot")

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
        self.quantize_symbol("WHITESPACE")
        self.quantize_symbol("LINEBREAK")

    @property
    def num_symbols(self) -> int:
        return len(self._quantized_symbols) + SpecialSymbols.count()

    def quantize_rule(self, rule: RawRule):
        def quantize_rule_symbol(symbol: str):
            nonlocal self
            if ss := SpecialSymbols.from_symbol(symbol):
                return ss.value[0]
            if se := SpecialSymbols.literal_from_escape(symbol):
                symbol = se
            return self.quantize_symbol(symbol)

        return QuantizedRule(
            quantize_rule_symbol(rule.symbol),
            [quantize_rule_symbol(symbol) for symbol in rule.rule],
            rule.options,
        )

    def quantize_symbol(self, symbol: str) -> int:
        if symbol.isspace():
            symbol = "LINEBREAK" if symbol == "\n" else "WHITESPACE"
        if symbol not in self._quantized_symbols:
            self._quantized_symbols[symbol] = self.num_symbols
        return self._quantized_symbols[symbol]

    def dequantize_symbol(self, quantized: int) -> Optional[str]:
        if quantized >= self.num_symbols:
            return None
        for s, qt in self._quantized_symbols.items():
            if qt == quantized:
                return s
        assert False
