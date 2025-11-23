from olive.parse.lexer.lexer import Lexer
from olive.parse.lexer.ast import QuantizedASTNode
from typing import ClassVar
from pathlib import Path

C_KEYWORDS = set(
    [
        "alignof",
        "auto",
        "break",
        "case",
        "const",
        "continue",
        "default",
        "do",
        "else",
        "enum",
        "extern",
        "for",
        "goto",
        "if",
        "include",
        "inline",
        "register",
        "restrict",
        "return",
        "sizeof",
        "static",
        "struct",
        "switch",
        "typedef",
        "union",
        "void",
        "volatile",
        "while",
    ]
)


class CLexer(Lexer):
    RULES_PATH: ClassVar[Path] = Path(__file__).parent / "c_lexer_rules.txt"

    def __init__(self):
        super().__init__()

        self._load_and_compile_rules(CLexer.RULES_PATH)
        self.register_special_rule(
            "CONSOLIDATE-IDENTIFIERS", self._special_rule__consolidate_identifiers
        )
        self.register_special_rule(
            "RESOLVE-KEYWORDS", self._special_rule__resolve_keywords
        )
        self.register_special_rule("PURGE-COMMENTS", self._special_rule__purge_comments)

    def _special_rule__consolidate_identifiers(self):
        identifier_symbol = self._language.quantize_symbol("IDENTIFIER")

        for idx in range(len(self._data)):
            node = self._data[idx]
            if node.symbol == identifier_symbol:
                self._data[idx] = QuantizedASTNode(
                    node.symbol, node.serialize(""), None
                )

    def _special_rule__resolve_keywords(self):
        identifier_symbol = self._language.quantize_symbol("IDENTIFIER")

        for idx in range(len(self._data)):
            node = self._data[idx]
            if node.symbol == identifier_symbol and node.value in C_KEYWORDS:
                symbol = f"KEYWORD__{node.value.upper()}"
                symbol = self._language.quantize_symbol(symbol)
                self._data[idx] = QuantizedASTNode(symbol, node.value, None)

    def _special_rule__purge_comments(self):
        groupings = []
        start_idx = -1

        start_symbol, end_symbol = self._language.quantize_symbol(
            "COMMENT_MULTI_START"
        ), self._language.quantize_symbol("COMMENT_MULTI_END")

        for idx, node in enumerate(self._data):
            if node.symbol == start_symbol:
                start_idx = idx
            elif node.symbol == end_symbol and start_idx >= 0:
                groupings.append((start_idx, idx))
                start_idx = -1

        last_idx = 0
        processed = []
        for s, e in groupings:
            processed.extend(self._data[last_idx:s])
            last_idx = e + 1
        processed.extend(self._data[last_idx:])

        self._data = processed
