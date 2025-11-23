from olive.parse.lexer.c_lexer import CLexer
from typing import ClassVar
from pathlib import Path


class StructLexer(CLexer):
    RULES_PATH: ClassVar[Path] = Path(__file__).parent / "struct_lexer_rules.txt"

    def __init__(self):
        super().__init__()

        self._load_and_compile_rules(StructLexer.RULES_PATH)

    def find_all_structures(self, path: Path):
        QT_STRUCT = self._language.quantize_symbol("STRUCT")
        nodes = self.parse_file(path)

        struct_nodes = [node for node in nodes if node.symbol == QT_STRUCT]

        return struct_nodes
