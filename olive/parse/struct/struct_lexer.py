from olive.parse.lexer.c_lexer import CLexer
from olive.parse.lexer.ast import QuantizedASTNode
from typing import ClassVar
from pathlib import Path


class StructLexer(CLexer):
    RULES_PATH: ClassVar[Path] = Path(__file__).parent / "struct_lexer_rules.txt"

    def __init__(self):
        super().__init__()

        self._load_and_compile_rules(StructLexer.RULES_PATH)

    def find_all_structures(self, path: Path) -> list[QuantizedASTNode]:
        QT_STRUCT = self._language.quantize_symbol("STRUCT")
        nodes = self.parse_file(path)

        struct_nodes = [node for node in nodes if node.symbol == QT_STRUCT]

        return struct_nodes


if __name__ == "__main__":
    sample_path = Path("/Users/jspencerpittman/Projects/Olive/sample/tmp.c")

    lexy = StructLexer()
    # res_quant = lexy.find_all_structures(sample_path)
    res_quant = lexy.parse_file(sample_path)
    from olive.parse.lexer.ast import RawASTNode
    from olive.parse.struct.description import StructDescription

    res = [
        RawASTNode.resolve_quantized_ast_tree(node, lexy._language)
        for node in res_quant
    ]

    for node in res_quant:
        res = RawASTNode.resolve_quantized_ast_tree(node, lexy._language)
        print(res.serialize_graph())
        # desc = StructDescription.parse_ast_struct(res)
        # print(desc.serialize())
