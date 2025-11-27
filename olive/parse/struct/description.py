from olive.parse.struct.struct_lexer import StructLexer
from olive.parse.lexer.ast import RawASTNode
from pathlib import Path
from time import time
from dataclasses import dataclass
from typing import Optional, Self


@dataclass
class VariableDescription(object):
    type_name: str
    name: str
    pointer_degree: int
    array_size: Optional[str]

    def serialize(self) -> str:
        return (
            self.type_name
            + f" {("*" * self.pointer_degree) + " " if self.pointer_degree > 0 else ""}"
            + self.name
            + (f"[{self.array_size}]" if self.array_size is not None else "")
        )

        return f"{self.type_name} {'*' * self.pointer_degree} {self.name}"

    @classmethod
    def parse_ast_variable(cls, node: RawASTNode) -> Optional[Self]:
        assert node.symbol == "VARIABLE"

        type_name = ""
        name = ""
        pointer_degree = 0
        array_size = None
        encountered_identifiers = 0

        if node.children is None:
            return None

        for child in node.children:
            match child.symbol:
                case "IDENTIFIER":
                    encountered_identifiers += 1
                    assert child.value is not None
                    if encountered_identifiers == 1:
                        type_name = child.value
                    elif encountered_identifiers == 2:
                        name = child.value
                    else:
                        return None
                case "*":
                    pointer_degree += 1
                case "ARRAY_BRACKET_CONSOLIDATED":
                    array_size = child.value
                case _:
                    continue

        return cls(type_name, name, pointer_degree, array_size)


@dataclass
class StructDescription(object):
    variables: list[VariableDescription]
    alias: Optional[str] = None
    typedef_alias: Optional[str] = None

    def serialize(self) -> str:
        return (
            f"struct {f'{self.alias} ' if self.alias else ''}"
            + "{\n"
            + "\n".join(["\t" + v.serialize() for v in self.variables])
            + "\n}"
            + (f" {self.typedef_alias}" if self.typedef_alias else "")
        )

    @classmethod
    def parse_ast_struct(cls, node: RawASTNode) -> Optional[Self]:
        assert node.symbol == "STRUCT"

        alias = None
        typedef_alias = None
        variables = []

        if node.children is not None:
            encountered_curly_brace = False
            open_curly_brace_cnt = 0

            for child in node.children:
                match child.symbol:
                    case "VARIABLE":
                        var = VariableDescription.parse_ast_variable(child)
                        if var is not None:
                            variables.append(var)
                    case "{":
                        open_curly_brace_cnt += 1
                        encountered_curly_brace = True
                    case "}":
                        open_curly_brace_cnt -= 1
                    case "IDENTIFIER":
                        if open_curly_brace_cnt == 0:
                            if encountered_curly_brace:
                                typedef_alias = child.value
                            else:
                                alias = child.value

                    case _:
                        continue

        return cls(variables, alias, typedef_alias)


"""
Driver
"""

if __name__ == "__main__":
    start = time()
    OUTPUT_PATH = Path(__file__).parent.parent / "lexer" / "lexen.txt"
    # SAMPLE_PATH = Path(__file__).parent.parent / "lexer" / "apply.c"
    SAMPLE_PATH = (
        Path(__file__).parent.parent.parent.parent
        / "sample/libgit2/src/libgit2"
        / "attrcache.h"
    )

    lexy = StructLexer()

    results = [
        RawASTNode.resolve_quantized_ast_tree(node, lexy._language)
        for node in lexy.find_all_structures(SAMPLE_PATH)
    ]
    with open(OUTPUT_PATH, "w") as outfile:
        for node in results:
            outfile.write(node.serialize_graph() + "\n\n")
            struct_desc = StructDescription.parse_ast_struct(node)
            if struct_desc is not None:
                print(struct_desc.serialize())

    # results = [
    #     RawASTNode.resolve_quantized_ast_tree(node, lexy._language)
    #     for node in lexy.parse_file(SAMPLE_PATH)
    # ]
    # with open(OUTPUT_PATH, "w") as outfile:
    #     for node in results:
    #         outfile.write(node.serialize_graph() + "\n\n")

    end = time()

    print(f"Duration: {end - start:.2f} Seconds")
