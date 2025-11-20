from dataclasses import dataclass
from olive.parse.regex.rules import QuantizedRule, RawRule
from olive.parse.regex.language import SpecialSymbols, Language
from olive.parse.regex.graph import Graph
from enum import Enum
from pathlib import Path


@dataclass
class Term(object):
    start: int
    end: int

    def __repr__(self) -> str:
        return f"{self.start} -> {self.end}"


class ThompsonConstructor(object):
    class Operation(Enum):
        NOT_AN_OPERATION = 0
        CONCATENATION = 1
        QUANTIFIER_ANY = 2
        QUANTIFIER_OPTIONAL = 3
        QUANTIFIER_AT_LEAST_ONE = 4
        COMPARISON_OR = 5

    @staticmethod
    def construct_rule(rule: QuantizedRule) -> tuple[Graph, Term]:
        def add_outer_concat(rule: list[int]):
            rule.insert(0, SpecialSymbols.LEFT_PAREN.value[0])
            rule.append(SpecialSymbols.RIGHT_PAREN.value[0])

        regex = rule.rule
        add_outer_concat(regex)
        graph = Graph()

        construction = ThompsonConstructor._construct_subrule(graph, regex)
        graph.mark_start_node(construction.start)
        graph.mark_node_association(construction.end, rule.symbol)
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
                case SpecialSymbols.ASTERISK:
                    return ThompsonConstructor.Operation.QUANTIFIER_ANY
                case SpecialSymbols.QUESTION_MARK:
                    return ThompsonConstructor.Operation.QUANTIFIER_OPTIONAL
                case SpecialSymbols.PLUS_SIGN:
                    return ThompsonConstructor.Operation.QUANTIFIER_AT_LEAST_ONE
                case SpecialSymbols.PIPE:
                    return ThompsonConstructor.Operation.COMPARISON_OR
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
            nested_rule = rule[1:outer_righ_paren_idx]

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
                    if open_paren_cnt == 0:
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
            nonlocal graph
            for a, b in zip(terms[:-1], terms[1:]):
                graph.add_edge(a.end, b.start, -1)
            return Term(terms[0].start, terms[-1].end)

        def hndl_quantifier_any(terms: list[Term]) -> Term:
            nonlocal graph
            inner_concat = hndl_concatenation(terms)
            start, end = inner_concat.start, inner_concat.end

            graph.add_edge(start, end, -1)
            graph.add_edge(end, start, -1)
            return Term(start, end)

        def hndl_quantifier_optional(terms: list[Term]) -> Term:
            nonlocal graph
            inner_concat = hndl_concatenation(terms)
            start, end = inner_concat.start, inner_concat.end

            graph.add_edge(start, end, -1)
            return Term(start, end)

        def hndl_quantifier_at_least_one(terms: list[Term]) -> Term:
            nonlocal graph
            inner_concat = hndl_concatenation(terms)
            start, end = inner_concat.start, inner_concat.end

            graph.add_edge(end, start, -1)
            return Term(start, end)

        def hndl_comparison_or(terms: list[Term]) -> Term:
            nonlocal graph
            start = graph.add_node()
            end = graph.add_node()

            for term in terms:
                graph.add_edge(start, term.start, -1)
                graph.add_edge(term.end, end, -1)

            return Term(start, end)

        operation = what_operation()
        if operation == ThompsonConstructor.Operation.NOT_AN_OPERATION:
            assert len(rule) == 1
            return create_simple_term(rule[0])

        terms = process_nested_terms()
        match operation:
            case ThompsonConstructor.Operation.CONCATENATION:
                return hndl_concatenation(terms)
            case ThompsonConstructor.Operation.QUANTIFIER_ANY:
                return hndl_quantifier_any(terms)
            case ThompsonConstructor.Operation.QUANTIFIER_OPTIONAL:
                return hndl_quantifier_optional(terms)
            case ThompsonConstructor.Operation.QUANTIFIER_AT_LEAST_ONE:
                return hndl_quantifier_at_least_one(terms)
            case ThompsonConstructor.Operation.COMPARISON_OR:
                return hndl_comparison_or(terms)

        assert False


if __name__ == "__main__":
    rules_path = Path(__file__).parent / "rules.txt"
    graph_path = Path(__file__).parent / "out_graph.txt"
    raw_rules = RawRule.load(rules_path)
    language = Language()
    quantized = [language.quantize_rule(rule) for rule in raw_rules]
    print(language._quantized_symbols)
    rg, rt = ThompsonConstructor.construct_rule(quantized[0])
    rg.write(graph_path)
    print(rt)
