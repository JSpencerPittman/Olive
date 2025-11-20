from dataclasses import dataclass
from olive.parse.regex.rules import QuantizedRule, RawRule
from olive.parse.regex.language import SpecialSymbols, Language
from enum import Enum
from pathlib import Path


@dataclass
class Term(object):
    start: int
    end: int

    def __repr__(self) -> str:
        return f"{self.start} -> {self.end}"


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
        return self.num_nodes - 1

    def write(self, path: Path):
        with open(path, "w") as outfile:
            for i in range(self.num_nodes):
                outfile.write(f"{i:<5d}: {self._graph[i]}\n")


class ThompsonConstructor(object):
    class Operation(Enum):
        NOT_AN_OPERATION = 0
        CONCATENATION = 1

    @staticmethod
    def construct_rule(rule: QuantizedRule) -> tuple[Graph, Term]:
        def add_outer_concat(rule: list[int]):
            rule.insert(0, SpecialSymbols.LEFT_PAREN.value[0])
            rule.append(SpecialSymbols.RIGHT_PAREN.value[0])

        regex = rule.rule
        add_outer_concat(regex)
        graph = Graph()

        construction = ThompsonConstructor._construct_subrule(graph, regex)
        return graph, construction

    @staticmethod
    def _construct_subrule(graph: Graph, rule: list[int]) -> Term:
        def what_operation() -> ThompsonConstructor.Operation:
            nonlocal rule

            if rule[0] != SpecialSymbols.LEFT_PAREN:
                return ThompsonConstructor.Operation.NOT_AN_OPERATION

            assert len(rule) >= 2
            match rule[-1]:
                case SpecialSymbols.RIGHT_PAREN:
                    return ThompsonConstructor.Operation.CONCATENATION
                case _:
                    assert False

        def create_simple_term(weight: int) -> Term:
            nonlocal graph
            src, tgt = graph.add_node(), graph.add_node()
            graph.add_edge(src, tgt, weight)
            return Term(src, tgt)

        def process_nested_terms() -> list[Term]:
            nonlocal rule

            # Determine aggregate bounds of nested terms
            outer_righ_paren_idx = len(rule) - 1
            while rule[outer_righ_paren_idx] != SpecialSymbols.RIGHT_PAREN:
                assert outer_righ_paren_idx >= 1
                outer_righ_paren_idx -= 1
            nested_rule_bound = slice(1, outer_righ_paren_idx)
            nested_rule = rule[nested_rule_bound]

            # Identify all first-tier terms
            groupings: list[tuple[int, int]] = []
            open_paren_cnt = 0
            open_paren_idx = -1
            for idx, sym in enumerate(nested_rule):
                if sym == SpecialSymbols.LEFT_PAREN:
                    open_paren_cnt += 1
                    if open_paren_cnt == 1:
                        open_paren_idx = idx
                elif sym == SpecialSymbols.RIGHT_PAREN:
                    open_paren_cnt -= 1
                    if open_paren_cnt == 0:
                        groupings.append((open_paren_idx, idx))
                        open_paren_idx = -1
                elif SpecialSymbols.is_special_symbol(sym):
                    # All other symbols are operands that need to be included in
                    # last added rule.
                    groupings[-1] = (groupings[-1][0], groupings[-1][1] + 1)
                else:
                    if open_paren_cnt == 0:
                        groupings.append((idx, idx))

            # Process each terms
            terms = []
            for gs, gf in groupings:
                terms.append(
                    ThompsonConstructor._construct_subrule(
                        graph, nested_rule[gs : gf + 1]
                    )
                )

            return terms

        def hndl_concatenation(terms: list[Term]) -> Term:
            for a, b in zip(terms[:-1], terms[1:]):
                graph.add_edge(a.end, b.start, -1)
            return Term(terms[0].start, terms[-1].end)

        operation = what_operation()
        if operation == ThompsonConstructor.Operation.NOT_AN_OPERATION:
            assert len(rule) == 1
            return create_simple_term(rule[0])

        terms = process_nested_terms()
        match operation:
            case ThompsonConstructor.Operation.CONCATENATION:
                return hndl_concatenation(terms)

        assert False


if __name__ == "__main__":
    rules_path = Path(__file__).parent / "rules.txt"
    graph_path = Path(__file__).parent / "out_graph.txt"
    raw_rules = RawRule.load(rules_path)
    language = Language()
    quantized = [language.quantize_rule(rule) for rule in raw_rules]
    rg, rt = ThompsonConstructor.construct_rule(quantized[0])
    rg.write(graph_path)
    print(rt)
