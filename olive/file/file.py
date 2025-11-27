from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class CharacterLeafNode:
    rem_value: str
    value: str


@dataclass
class CharacterNode:
    _mapping: dict[str, Union["CharacterNode", CharacterLeafNode]]

    def add_string(self, value: str):
        self._add_string_recursive(value, value)

    def gather_first_n_matches(self, value: str, n: int) -> list[str]:
        result = self._next_recursive(value)
        if isinstance(result, CharacterNode):
            return result._gather_first_n_matches_recursive(n)
        elif isinstance(result, str):
            return [result]
        else:
            return []

    def print(self):
        self._print_recursive(0)

    """
    Recursive Implementations
    """

    def _gather_first_n_matches_recursive(self, n: int) -> list[str]:
        assert self._mapping is not None
        matches = []
        remaining = n
        keys = sorted(self._mapping.keys())
        for k in keys:
            child = self._mapping[k]
            if isinstance(child, CharacterLeafNode):
                matches.append(child.value)
                remaining -= 1
            else:
                new_matches = child._gather_first_n_matches_recursive(remaining)
                matches.extend(new_matches)
                remaining -= len(new_matches)
            if remaining == 0:
                break

        return matches

    def _add_string_recursive(self, rem_value: str, value: str):
        if len(rem_value) == 0:
            self._mapping[""] = CharacterLeafNode("", value)
            return
        branch_value = rem_value[0]

        if branch_value not in self._mapping:
            self._mapping[branch_value] = CharacterLeafNode(rem_value[1:], value)
            return

        next_node = self._mapping[branch_value]
        if isinstance(next_node, CharacterLeafNode):
            # Replace leaf node with nonterminal node
            if len(next_node.rem_value) == 0:
                new_node = CharacterNode({"": CharacterLeafNode("", next_node.value)})
            else:
                new_node = CharacterNode(
                    {
                        next_node.rem_value[0]: CharacterLeafNode(
                            next_node.rem_value[1:], next_node.value
                        )
                    }
                )
            self._mapping[branch_value] = new_node

        # Add new string
        next_node = self._mapping[branch_value]
        assert isinstance(next_node, CharacterNode)
        next_node._add_string_recursive(rem_value[1:], value)

    def _next_recursive(self, rem_query: str) -> Optional[Union["CharacterNode", str]]:
        if len(rem_query) == 0:
            return self

        branch_value = rem_query[0]
        if branch_value not in self._mapping:
            return None

        next_node = self._mapping[branch_value]
        if isinstance(next_node, CharacterLeafNode):
            return next_node.value
        else:
            return next_node._next_recursive(rem_query[1:])

    def _print_recursive(self, tabs: int):
        for k, v in self._mapping.items():
            print("\t" * tabs + k)
            if isinstance(v, CharacterNode):
                v._print_recursive(tabs + 1)
            else:
                print("\t" * tabs, (v.rem_value, v.value))


class FileTree(object):
    @dataclass
    class FilePath(object):
        name: str
        proj_path: Path
        proj_dir: Path

        @property
        def full_path(self) -> Path:
            return self.proj_dir / self.proj_path

        def to_json(self) -> dict:
            return {
                "name": self.name,
                "proj_path": str(self.proj_path),
                "proj_dir": str(self.proj_dir),
                "full_path": str(self.full_path),
            }

    def __init__(self, proj_dir: Path):
        self.proj_dir = proj_dir
        self._name_to_path: dict[str, list[FileTree.FilePath]] = {}
        self._search_tree = CharacterNode({})

    def index_files(self):
        for file in self.proj_dir.glob("**/*.[c|h]"):
            name, rel_path = file.name, file.relative_to(self.proj_dir)
            fp = FileTree.FilePath(name, rel_path, self.proj_dir)
            if name in self._name_to_path:
                self._name_to_path[name].append(fp)
            else:
                self._name_to_path[name] = [fp]
            self._search_tree.add_string(name)

    def search(self, name: str, n: int) -> list[FilePath]:
        results = []
        for match in self._search_tree.gather_first_n_matches(name, n):
            results.extend(self._name_to_path[match])
        return results
