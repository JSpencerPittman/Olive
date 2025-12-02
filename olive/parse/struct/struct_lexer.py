from olive.parse.lexer.c_lexer import CLexer
from olive.parse.lexer.ast import QuantizedASTNode
from olive.parse.regex.rules import parse_rule_from_str
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

    def _special_rule__capture_nested_defs(self):
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
        prev_length = len(self._data)
        while True:
            self._run_qt_rule(qt_rule__union, rule_graph__union)
            self._run_qt_rule(qt_rule__struct, rule_graph__struct)
            if len(self._data) == prev_length:
                break
            prev_length = len(self._data)

    def _special_rule__consolidate_enum_contents(self):
        enum_groupings = self._utility__find_groups("ENUM__START", "}")
        equal_groupings = self._utility__find_groups(
            "=", ","
        ) + self._utility__find_groups("=", "}")

        def is_nested(sub_group: tuple[int, int], parent_group: tuple[int, int]):
            return parent_group[0] <= sub_group[0] and sub_group[1] <= parent_group[1]

        filtered = []
        for enum_group in enum_groupings:
            for equal_group in equal_groupings:
                if is_nested(equal_group, enum_group):
                    filtered.append(equal_group)

        self._utility__consolidate_groups(filtered, "ENUM_CONTENTS", (True, False))


if __name__ == "__main__":
    sample_path = Path("/Users/jspencerpittman/Projects/Olive/sample/tmp.c")

    lexy = StructLexer()
    # res_quant = lexy.find_all_structures(sample_path)
    res_quant = lexy.parse_file(sample_path)
    from olive.parse.lexer.ast import RawASTNode
    from olive.parse.struct.description_dep import StructDescription

    res = [
        RawASTNode.resolve_quantized_ast_tree(node, lexy._language)
        for node in res_quant
    ]

    for node in res_quant:
        res = RawASTNode.resolve_quantized_ast_tree(node, lexy._language)
        print(res.serialize_graph())
        # desc = StructDescription.parse_ast_struct(res)
        # print(desc.serialize())
