from olive.parse.struct.description import (
    StructDescription,
    VariableDescription,
    UnionDescription,
)
from typing import Optional


class ReferencingStructDescription(StructDescription):
    def __init__(
        self,
        members: list[VariableDescription | UnionDescription],
        alias: Optional[str] = None,
        typedef_alias: Optional[str] = None,
    ):
        def _gather_references() -> list[str]:
            nonlocal self
            references = []

            for member in self.members:
                if isinstance(member, VariableDescription):
                    references.append(member.type_name)
                else:
                    for u_member in member.members:
                        references.append(u_member.type_name)

            return references

        super().__init__(members, alias, typedef_alias)
        self._references = _gather_references()
        self.existing_references: set[str] = set([])

    @classmethod
    def from_reg_struct_desc(cls, reg: StructDescription):
        return cls(reg.members, reg.alias, reg.typedef_alias)

    @property
    def name(self) -> Optional[str]:
        if self.typedef_alias is not None:
            return self.typedef_alias
        elif self.alias is not None:
            return f"struct {self.alias}"
        return None

    def is_referenced(self, referred: "ReferencingStructDescription") -> bool:
        struct_names = []
        if referred.typedef_alias is not None:
            struct_names.append(referred.typedef_alias)
        if referred.alias is not None:
            struct_names.append(f"struct {referred.alias}")
        if len(struct_names) == 0:
            return False

        for reference in self._references:
            if reference in struct_names:
                return True

        return False

    def update_references(self, referred: "ReferencingStructDescription"):
        if self.is_referenced(referred):
            assert referred.name is not None
            self.existing_references.add(referred.name)

    def to_json(self) -> dict:
        return {
            "name": self.name,
            "references": list(self.existing_references),
            "serialized": self.serialize(),
        }

    def __eq__(self, value) -> bool:
        if not isinstance(value, StructDescription):
            return False

        if self.typedef_alias is not None or value.typedef_alias is not None:
            return self.typedef_alias == value.typedef_alias

        if self.alias is not None or value.alias is not None:
            return self.alias == value.alias

        return self.serialize() == value.serialize()


class ReferencingStructDescriptionSet(object):
    def __init__(self):
        self._structs = []

    def add_struct(self, struct: ReferencingStructDescription):
        if struct not in self._structs:
            self._structs.append(struct)
            self._update_references_wrt_latest_node()

    def get_struct(self, name: str) -> Optional[ReferencingStructDescription]:
        for struct in self._structs:
            if struct.name == name:
                return struct
        return None

    def __iter__(self):
        return iter(self._structs)

    def _update_references_wrt_latest_node(self):
        # Update other nodes
        for struct in self._structs[:-1]:
            struct.update_references(self._structs[-1])
            self._structs[-1].update_references(struct)
