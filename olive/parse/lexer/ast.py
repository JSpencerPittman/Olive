from dataclasses import dataclass
from typing import Optional, TypeVar, Generic, Self
from olive.parse.regex.language import Language
from abc import ABC


T = TypeVar("T")


@dataclass
class ASTNode(ABC, Generic[T]):
    symbol: T
    lines: tuple[int, int]
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
        raw_root = cls(raw_sym, qt_root.lines, qt_root.value)

        if qt_root.children is not None:
            raw_root.children = []
            for qt_child in qt_root.children:
                raw_root.children.append(
                    cls.resolve_quantized_ast_tree(qt_child, language)
                )

        return raw_root

    def get_first_child(self, symbol: str) -> Optional[Self]:
        if self.symbol == symbol:
            return self
        if self.children is not None:
            for child in self.children:
                if (tgt := child.get_first_child(symbol)) is not None:
                    return tgt
        return None

    def get_nth_child(self, symbol: str, n: int) -> Optional[Self]:
        remaining, match = self._get_nth_child_recursive(symbol, n)
        if remaining == 0:
            return match
        else:
            return None

    def does_child_exist(self, symbol: str) -> bool:
        return self.get_first_child(symbol) is not None

    def _get_nth_child_recursive(
        self, symbol: str, remaining: int
    ) -> tuple[int, Optional[Self]]:
        if self.symbol == symbol:
            remaining -= 1
            if remaining == 0:
                return (0, self)

        if self.children is None:
            return (remaining, None)

        for child in self.children:
            rem, match = child._get_nth_child_recursive(symbol, remaining)
            if rem == 0:
                return (0, match)
            remaining = rem
        return (remaining, None)
