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
        "define",
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
        self.register_special_rule(
            "CONSOLIDATE-DEFINE-CONTENTS",
            self._special_rule__consolidate_define_contents,
        )
        self.register_special_rule(
            "CONSOLIDATE-ARRAY-BRACKETS", self._special_rule__consolidate_array_brackets
        )

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
        groupings = self._special_rule_utility__find_open_close_groups(
            "COMMENT_MULTI_START", "COMMENT_MULTI_END"
        )

        last_idx = 0
        processed = []
        for s, e in groupings:
            processed.extend(self._data[last_idx:s])
            last_idx = e + 1
        processed.extend(self._data[last_idx:])

        self._data = processed

    def _special_rule__consolidate_define_contents(self):
        # Pre-existing
        QT_DEFINE_START = self._language.quantize_symbol("DEFINE_START")
        QT_WHITESPACE = self._language.quantize_symbol("WHITESPACE")
        QT_LINE_EXTENSION = self._language.quantize_symbol("\\")
        QT_LINEBREAK = self._language.quantize_symbol("\n")

        # New token
        QT_DEFINE_CONSOLIDATED = self._language.quantize_symbol("DEFINE_CONSOLIDATED")

        # Identify groups to be consolidated
        groupings = []
        start_idx = -1
        extension = False
        for idx, token in enumerate(self._data):
            if token.symbol == QT_DEFINE_START:
                start_idx = idx + 1
                token.children = [
                    child for child in token.children if child.symbol != QT_WHITESPACE
                ]
            elif token.symbol == QT_LINE_EXTENSION:
                extension = True
            elif token.symbol == QT_LINEBREAK:
                if start_idx >= 0 and not extension:
                    groupings.append((start_idx, idx))
                    start_idx = -1
                extension = False
        if start_idx >= 0:
            groupings.append((start_idx, len(self._data)))

        # Process groups
        last_idx = 0
        processed = []
        for s, e in groupings:
            processed.extend(self._data[last_idx:s])
            if s + 1 != e:
                processed.append(
                    QuantizedASTNode(
                        QT_DEFINE_CONSOLIDATED,
                        (
                            "".join(
                                [node.serialize("") for node in self._data[s + 1 : e]]
                            )
                        ).strip(),
                    )
                )
            last_idx = e + 1
        processed.extend(self._data[last_idx:])

        self._data = processed

    def _special_rule__consolidate_array_brackets(self):
        groupings = self._special_rule_utility__find_open_close_groups("[", "]")
        QT_ARRAY_CONSOLIDATED = self._language.quantize_symbol(
            "ARRAY_BRACKET_CONSOLIDATED"
        )

        last_idx = 0
        processed = []
        for s, e in groupings:
            processed.extend(self._data[last_idx:s])
            if s + 1 != e:
                processed.append(
                    QuantizedASTNode(
                        QT_ARRAY_CONSOLIDATED,
                        "".join([node.serialize("") for node in self._data[s + 1 : e]]),
                    )
                )
            last_idx = e + 1
        processed.extend(self._data[last_idx:])

        self._data = processed

    def _special_rule_utility__find_open_close_groups(
        self, start_sym: str, end_sym: str
    ) -> list[tuple[int, int]]:
        groupings = []
        start_idx = -1

        start_symbol = self._language.quantize_symbol(start_sym)
        end_symbol = self._language.quantize_symbol(end_sym)

        for idx, node in enumerate(self._data):
            if node.symbol == start_symbol:
                start_idx = idx
            elif node.symbol == end_symbol and start_idx >= 0:
                groupings.append((start_idx, idx))
                start_idx = -1

        return groupings
