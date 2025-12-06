from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar, Optional, Self, Type

from olive.parse.lexer.ast import RawASTNode
from olive.parse.struct.struct_lexer import StructLexer


class Description(ABC):
    _AST_NAME: ClassVar[str] = ""

    @abstractmethod
    def serialize(self) -> str: ...

    @classmethod
    @abstractmethod
    def from_ast(cls, node: RawASTNode) -> Optional[Self | list[Self]]: ...

    @classmethod
    def is_ast_node_of_this_type(cls, node: RawASTNode) -> bool:
        return node.symbol == cls._AST_NAME


@dataclass
class VariableDescription(Description):
    _AST_NAME: ClassVar[str] = "VARIABLE__DEC"

    is_static: bool
    is_const: bool
    is_struct: bool
    is_unsigned: bool
    type_name: str
    pointer_degree: int
    name: str
    array_contents: Optional[str]

    def serialize(self) -> str:
        return (
            ("static " if self.is_static else "")
            + ("const " if self.is_const else "")
            + ("struct " if self.is_struct else "")
            + ("unsigned " if self.is_unsigned else "")
            + self.type_name
            + " "
            + (f"{'*' * self.pointer_degree} " if self.pointer_degree > 0 else "")
            + self.name
            + (f"[{self.array_contents}]" if self.array_contents is not None else "")
            + ";"
        )

    @classmethod
    def from_ast(cls, node: RawASTNode) -> list[Self]:
        assert node.symbol == VariableDescription._AST_NAME

        def from__variable_incomplete(cls: Type[Self], node: RawASTNode) -> Self:
            assert node.symbol == "VARIABLE__INCOMPLETE"
            is_static = node.does_child_exist("KEYWORD__STATIC")
            is_const = node.does_child_exist("KEYWORD__CONST")
            is_struct = node.does_child_exist("KEYWORD__STRUCT")
            is_unsigned = node.does_child_exist("KEYWORD__UNSIGNED")

            # Type name
            child = node.get_first_child("IDENTIFIER")
            assert child is not None and child.value is not None
            type_name = child.value

            # Pointer degree
            assert node.children is not None
            pointer_degree = 0
            for child in node.children:
                if child.symbol == "*":
                    pointer_degree += 1

            # Name
            child = node.get_nth_child("IDENTIFIER", 2)
            assert child is not None and child.value is not None
            name = child.value

            # Array Contents
            child = node.get_first_child("ARRAY_BRACKET_CONSOLIDATED")
            array_contents = None if child is None else child.value

            return cls(
                is_static,
                is_const,
                is_struct,
                is_unsigned,
                type_name,
                pointer_degree,
                name,
                array_contents,
            )

        def from__variable_comma_dec(cls: Type[Self], node: RawASTNode) -> list[Self]:
            assert node.symbol == "VARIABLE__COMMA_DEC"
            assert node.children is not None

            # Parse base variable
            variable_incomplete_node = node.get_first_child("VARIABLE__INCOMPLETE")
            assert variable_incomplete_node is not None
            base_variable = from__variable_incomplete(cls, variable_incomplete_node)

            # Parse each variable
            variables = [base_variable]

            pointer_degree = 0
            name = ""
            array_contents = None

            for child in node.children:
                match child.symbol:
                    case "*":
                        pointer_degree += 1
                    case "IDENTIFIER":
                        assert child.value is not None
                        name = child.value
                    case "ARRAY_BRACKET_CONSOLIDATED":
                        assert child.value is not None
                        array_contents = child.value
                    case ",":
                        variables.append(
                            cls(
                                base_variable.is_static,
                                base_variable.is_const,
                                base_variable.is_struct,
                                base_variable.is_unsigned,
                                base_variable.type_name,
                                pointer_degree,
                                name,
                                array_contents,
                            )
                        )
                        pointer_degree = 0
                        name = ""
                        array_contents = None
            variables.append(
                cls(
                    base_variable.is_static,
                    base_variable.is_const,
                    base_variable.is_struct,
                    base_variable.is_unsigned,
                    base_variable.type_name,
                    pointer_degree,
                    name,
                    array_contents,
                )
            )

            return variables

        if (
            variable_semicolon_term_node := node.get_first_child(
                "VARIABLE__SEMICOLON_TERM"
            )
        ) is not None:
            variable_incomplete_node = variable_semicolon_term_node.get_first_child(
                "VARIABLE__INCOMPLETE"
            )
            assert variable_incomplete_node is not None
            return [from__variable_incomplete(cls, variable_incomplete_node)]
        else:
            variable_comma_dec_node = node.get_first_child("VARIABLE__COMMA_DEC")
            assert variable_comma_dec_node is not None
            return from__variable_comma_dec(cls, variable_comma_dec_node)


@dataclass
class ContainerDescription(Description):
    name: Optional[str]
    children: list[Description]
    alias: list[str]

    @classmethod
    def _container_from_ast(cls, node: RawASTNode) -> Self:
        assert node.children is not None

        name = None
        children: list[Description] = []
        alias = []

        encountered_curlies = 0
        for child in node.children:
            match child.symbol:
                case "{":
                    encountered_curlies += 1
                case "}":
                    encountered_curlies += 1
                case "IDENTIFIER":
                    if encountered_curlies == 0:
                        assert child.value is not None
                        name = child.value
                    elif encountered_curlies == 2:
                        assert child.value is not None
                        alias.append(child.value)
                    else:
                        assert False
                case "VARIABLE__DEC":
                    children.extend(VariableDescription.from_ast(child))
                case "STRUCT__DEF":
                    children.append(StructDescription.from_ast(child))
                case "UNION__DEF":
                    children.append(UnionDescription.from_ast(child))

        return cls(name, children, alias)

    def _container_serialize(self, container_keyword: str) -> str:
        members = []
        for member in self.children:
            if isinstance(member, VariableDescription):
                members.append("\t" + member.serialize())
            else:
                members.append(
                    "\n".join(["\t" + line for line in member.serialize().split("\n")])
                )

        return (
            container_keyword
            + " "
            + (f"{self.name} " if self.name is not None else "")
            + "{\n"
            + "\n".join(members)
            + ("\n" if len(members) else "")
            + "}"
            + (" " + " ,".join(self.alias) if len(self.alias) else "")
            + ";"
        )


class UnionDescription(ContainerDescription):
    _AST_NAME = "UNION__DEF"

    name: Optional[str]
    children: list
    alias: list[str]

    @classmethod
    def from_ast(cls, node: RawASTNode) -> Self:
        assert node.symbol == UnionDescription._AST_NAME
        return cls._container_from_ast(node)

    def serialize(self) -> str:
        return self._container_serialize("union")


class StructDescription(ContainerDescription):
    _AST_NAME = "STRUCT__DEF"

    @classmethod
    def from_ast(cls, node: RawASTNode) -> Self:
        assert node.symbol == StructDescription._AST_NAME
        return cls._container_from_ast(node)

    def serialize(self) -> str:
        return self._container_serialize("struct")


@dataclass
class TypedefReferenceDescription(Description):
    _AST_NAME: ClassVar[str] = "TYPEDEF__REF"
    is_struct: bool
    desc: VariableDescription

    @property
    def is_union(self) -> bool:
        return not self.is_struct

    @classmethod
    def from_ast(cls, node: RawASTNode) -> Self:
        assert node.symbol == StructDescription._AST_NAME
        is_struct = node.does_child_exist("KEYWORD_STRUCT")
        desc_ast = node.get_first_child("VARIABLE__DEC")
        assert desc_ast is not None
        desc = VariableDescription.from_ast(desc_ast)
        return cls(is_struct, desc[0])

    def serialize(self) -> str:
        return (
            "typedef "
            + ("struct " if self.is_struct else "union ")
            + self.desc.serialize()
        )


DESCRIPTION_CLASSES: list[Type[Description]] = [
    VariableDescription,
    UnionDescription,
    StructDescription,
    TypedefReferenceDescription,
]


def description_from_ast(node: RawASTNode) -> Optional[Description | list[Description]]:
    if node.symbol == "TYPEDEF__DEF":
        assert node.children is not None
        node = node.children[1]

    for desc_class in DESCRIPTION_CLASSES:
        if desc_class.is_ast_node_of_this_type(node):
            return desc_class.from_ast(node)

    return None


def find_structs(path: Path) -> list[StructDescription]:
    structs = []
    lexy = StructLexer()

    results_qt = lexy.parse_file(path)
    with open("log__parsed.txt", "w") as ofile:
        for result in results_qt:
            result_raw = RawASTNode.resolve_quantized_ast_tree(result, lexy._language)
            ofile.write(result_raw.serialize_graph() + "\n\n")
    # for struct in lexy.find_all_structures(path):
    #     raw_struct = RawASTNode.resolve_quantized_ast_tree(struct, lexy._language)
    #     struct_desc = StructDescription.from_ast(raw_struct)
    #     if struct_desc is not None:
    #         structs.append(struct_desc)
    return structs


if __name__ == "__main__":
    from pathlib import Path

    from olive.parse.struct.struct_lexer import StructLexer

    sample_path = Path("/Users/jspencerpittman/Projects/Olive/sample/tmp.c")

    lexy = StructLexer()
    res_quant = lexy.parse_file(sample_path)

    res = [
        RawASTNode.resolve_quantized_ast_tree(node, lexy._language)
        for node in res_quant
    ]

    for node in res_quant:
        res_deq = RawASTNode.resolve_quantized_ast_tree(node, lexy._language)
        desc_res = description_from_ast(res_deq)
        if desc_res is not None:
            if not isinstance(desc_res, list):
                desc_res = [desc_res]
            for d in desc_res:
                print(d.serialize())
