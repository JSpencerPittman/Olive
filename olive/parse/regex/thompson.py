from dataclasses import dataclass
from olive.parse.regex.rules import QuantizedRule
from olive.parse.regex.language import SpecialSymbols
from enum import Enum


@dataclass
class Term(object):
    start: int
    end: int


class Graph(object):
    def __init__(self):
        self._graph = {}

    @property
    def num_nodes(self) -> int:
        return len(self._graph)

    def add_edge(self, src: int, tgt: int, choice: int):
        assert src in self._graph
        self._graph[src].append((tgt, choice))

    def add_node(self) -> int:
        self._graph[self.num_nodes] = []
        return self.num_nodes


class ThompsonConstructor(object):
    class Operation(Enum):
        NOT_AN_OPERATION = 0
        CONCATENATION = 1

    @staticmethod
    def construct_rule(rule: QuantizedRule):
        def add_outer_concat(rule: list[int]):
            rule.insert(0, SpecialSymbols.LEFT_PAREN.value[0])
            rule.append(SpecialSymbols.RIGHT_PAREN.value[0])

        regex = rule.rule
        add_outer_concat(regex)

    @staticmethod
    def construct_subrule(graph: Graph, rule: list[int]) -> Term:
        def what_operation() -> ThompsonConstructor.Operation:
            nonlocal rule
            if rule[0] != SpecialSymbols.LEFT_PAREN:
                return ThompsonConstructor.Operation.NOT_AN_OPERATION

            assert len(rule) >= 2
            operand = rule[-1]
            match operand:
                case SpecialSymbols.RIGHT_PAREN:
                    return ThompsonConstructor.Operation.CONCATENATION
                case _:
                    assert False

        def create_simple_term(weight: int) -> Term:
            nonlocal graph
            src, tgt = graph.add_node(), graph.add_node()
            graph.add_edge(src, tgt, weight)
            return Term(src, tgt)

        def process_nested_terms(): ...

        def hndl_concatenation(): ...

        operation = what_operation()
        if operation == ThompsonConstructor.Operation.NOT_AN_OPERATION:
            assert len(rule) == 1
            return create_simple_term(rule[0])
        # elif operation == ThompsonConstructor.Operation.CONCATENATION:
        # return create_simple_term(rule[0])
        else:
            assert False
