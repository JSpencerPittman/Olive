from olive.parse.lexer.lexer import Lexer
from olive.parse.lexer.ast import QuantizedASTNode
from olive.parse.regex.language import Language
from olive.parse.regex.rules import SpecialRule
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
        "ifndef",
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
        "unsigned",
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

    def _special_rule__consolidate_identifiers(self, rule: SpecialRule):
        identifier_symbol = self._language.quantize_symbol("IDENTIFIER")

        buffer = self._repo.load(rule)
        for idx in range(len(buffer)):
            node = buffer[idx]
            if node.symbol == identifier_symbol:
                buffer[idx] = QuantizedASTNode(
                    node.symbol, node.lines, node.serialize(""), None
                )
        self._repo.save(rule, buffer)

    def _special_rule__resolve_keywords(self, rule: SpecialRule):
        identifier_symbol = self._language.quantize_symbol("IDENTIFIER")

        buffer = self._repo.load(rule)
        for idx in range(len(buffer)):
            node = buffer[idx]
            if node.symbol == identifier_symbol and node.value in C_KEYWORDS:
                symbol = f"KEYWORD__{node.value.upper()}"
                qt_symbol = self._language.quantize_symbol(symbol)
                buffer[idx] = QuantizedASTNode(qt_symbol, node.lines, node.value, None)
        self._repo.save(rule, buffer)

    def _special_rule__purge_comments(self, rule: SpecialRule):
        groupings = self._special_rule_utility__find_open_close_groups(
            rule, "COMMENT_MULTI_START", "COMMENT_MULTI_END"
        )

        last_idx = 0
        processed = []
        buffer = self._repo.load(rule)
        for s, e in groupings:
            processed.extend(buffer[last_idx:s])
            last_idx = e + 1
        processed.extend(buffer[last_idx:])

        self._repo.save(rule, processed)

    def _special_rule__consolidate_define_contents(self, rule: SpecialRule):
        def is_end(symbol: int, state: dict, language: Language) -> tuple[bool, dict]:
            if len(state.keys()) == 0:
                state["QT_LINE_EXTENSION"] = language.quantize_symbol("\\")
                state["QT_LINEBREAK"] = language.quantize_symbol("\n")
                state["EXTENSION"] = False

            status = False
            if symbol == state["QT_LINE_EXTENSION"]:
                state["EXTENSION"] = True
            elif symbol == state["QT_LINEBREAK"]:
                if not state["EXTENSION"]:
                    status = True
                state["EXTENSION"] = False

            return status, state

        groups = self._utility__find_groups(rule, "DEFINE_START", is_end_func=is_end)
        self._utility__consolidate_groups(
            rule, groups, "DEFINE_CONSOLIDATED", (False, True)
        )

    def _special_rule_utility__find_open_close_groups(
        self, rule: SpecialRule, start_sym: str, end_sym: str
    ) -> list[tuple[int, int]]:
        groupings = []
        start_idx = -1

        start_symbol = self._language.quantize_symbol(start_sym)
        end_symbol = self._language.quantize_symbol(end_sym)

        for idx, node in enumerate(self._repo.load(rule)):
            if node.symbol == start_symbol:
                start_idx = idx
            elif node.symbol == end_symbol and start_idx >= 0:
                groupings.append((start_idx, idx))
                start_idx = -1

        return groupings
