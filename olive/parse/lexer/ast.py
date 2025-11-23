from dataclasses import dataclass
from typing import Optional, TypeVar, Generic, Self
from olive.parse.regex.language import Language
from abc import ABC


T = TypeVar("T")


@dataclass
class ASTNode(ABC, Generic[T]):
    symbol: T
    value: Optional[str]
    children: Optional[list[Self]] = None

    def serialize(self, join_char: str = " ") -> str:
        if self.children is None:
            return self.value if self.value is not None else ""
        return join_char.join([child.serialize(join_char) for child in self.children])


@dataclass
class QuantizedASTNode(ASTNode[int]):
    symbol: int
    value: Optional[str]


@dataclass
class RawASTNode(ASTNode[str]):
    symbol: str
    value: Optional[str]

    def serialize_graph(self) -> str:
        return "\n".join(self._serialize_graph_recursive())

    def _serialize_graph_recursive(self) -> list[str]:
        def tab_all_lines(lines: list[str]):
            for idx in range(len(lines)):
                lines[idx] = "\t" + lines[idx]

        if self.children is None or len(self.children) == 0:
            return [f"{self.symbol}: {self.value}"]

        result = [f"{self.symbol}"]
        for child in self.children:
            child_res = child._serialize_graph_recursive()
            tab_all_lines(child_res)
            result += child_res

        return result

    @classmethod
    def resolve_quantized_ast_tree(
        cls, qt_root: QuantizedASTNode, language: Language
    ) -> Self:
        raw_sym = language.dequantize_symbol(qt_root.symbol)
        assert raw_sym is not None
        raw_root = cls(raw_sym, qt_root.value)

        if qt_root.children is not None:
            raw_root.children = []
            for qt_child in qt_root.children:
                raw_root.children.append(
                    cls.resolve_quantized_ast_tree(qt_child, language)
                )

        return raw_root
