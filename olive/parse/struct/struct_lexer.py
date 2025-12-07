from olive.parse.lexer.c_lexer import CLexer
from olive.parse.lexer.ast import QuantizedASTNode
from olive.parse.regex.rules import parse_rule_from_str, SpecialRule
from olive.parse.regex.thompson import ThompsonConstructor
from typing import ClassVar
from pathlib import Path


class StructLexer(CLexer):
    RULES_PATH: ClassVar[Path] = Path(__file__).parent / "struct_lexer_rules.txt"

    def __init__(self):
        super().__init__()

        self._load_and_compile_rules(StructLexer.RULES_PATH)

        self.register_special_rule(
            "CAPTURE-NESTED-DEFS", self._special_rule__capture_nested_defs
        )
        self.register_special_rule(
            "CONSOLIDATE-ENUM-CONTENTS", self._special_rule__consolidate_enum_contents
        )

    def find_all_structures(self, path: Path) -> list[QuantizedASTNode]:
        QT_STRUCT = self._language.quantize_symbol("STRUCT")
        nodes = self.parse_file(path)

        struct_nodes = [node for node in nodes if node.symbol == QT_STRUCT]

        return struct_nodes

    def _special_rule__capture_nested_defs(self, rule: SpecialRule):
        nesting_capture_rule_str__union = (
            "UNION__DEF := KEYWORD__UNION ( IDENTIFIER ) ? { ( ( "
            "VARIABLE__DEC UNION__DEF STRUCT__DEF ) | ) * } ( IDENTIFIER ) ? ;"
        )
        nesting_capture_rule_str__struct = (
            "STRUCT__DEF := KEYWORD__STRUCT ( IDENTIFIER ) ? { ( ( "
            "VARIABLE__DEC UNION__DEF STRUCT__DEF ) | ) * } ( IDENTIFIER ) ? ;"
        )

        nesting_capture_rule_raw__union = parse_rule_from_str(
            nesting_capture_rule_str__union
        )
        nesting_capture_rule_raw__struct = parse_rule_from_str(
            nesting_capture_rule_str__struct
        )
        qt_rule__union = self._language.quantize_rule(nesting_capture_rule_raw__union)
        qt_rule__struct = self._language.quantize_rule(nesting_capture_rule_raw__struct)
        rule_graph__union = ThompsonConstructor.construct_rule(qt_rule__union)
        rule_graph__struct = ThompsonConstructor.construct_rule(qt_rule__struct)

        # Keep looping until no more nested definitions are captured
        buffer = self._repo.load(rule)
        prev_length = len(buffer)
        while True:
            self._run_qt_rule(qt_rule__union, rule_graph__union)
            self._run_qt_rule(qt_rule__struct, rule_graph__struct)
            if len(buffer) == prev_length:
                break
            prev_length = len(buffer)

    def _special_rule__consolidate_enum_contents(self, rule: SpecialRule):
        QT_EQUAL = self._language.quantize_symbol("=")
        QT_COMMA = self._language.quantize_symbol(",")

        buffer = self._repo.load(rule)
        enum_groupings = self._utility__find_groups(rule, "ENUM__START", "}")
        content_groupings = []
        for start, end in enum_groupings:
            start_idx = -1
            for idx, node in enumerate(buffer[start:end]):
                if node.symbol == QT_EQUAL:
                    start_idx = start + idx
                elif node.symbol == QT_COMMA:
                    if start_idx >= 0:
                        content_groupings.append((start_idx, start + idx))
                        start_idx = -1
            if start_idx >= 0:
                content_groupings.append((start_idx, end))

        self._utility__consolidate_groups(
            rule, content_groupings, "ENUM_CONTENTS", (True, False)
        )
