from pathlib import Path
from typing import Callable, ClassVar, Optional
from copy import deepcopy

from olive.parse.regex.graph import GraphTraveler, Graph
from olive.parse.regex.language import Language
from olive.parse.regex.rules import SpecialRule, QuantizedRule, load_rules, Rule
from olive.parse.regex.thompson import ThompsonConstructor
from olive.parse.lexer.ast import QuantizedASTNode


class LexerDataRepository(object):
    def __init__(self):
        self._data = {}

    def load(self, rule: QuantizedRule | str) -> list[QuantizedASTNode]:
        branch_name = rule if isinstance(rule, str) else rule.options.load
        return deepcopy(self._data[branch_name])

    def new_branch(self, name: str, data: list[QuantizedASTNode]):
        self._data[name] = deepcopy(data)

    def save(self, rule: QuantizedRule, data: list[QuantizedASTNode]):
        if rule.options.load == rule.options.save:
            self._data[rule.options.save] = deepcopy(data)
        else:
            self._merge(rule.options.load, rule.options.save, rule.symbol)

    def _merge(self, from_name: str, to_name: str, qt_symbol: int):
        def overlap(node1: QuantizedASTNode, node2: QuantizedASTNode) -> bool:
            n1s, n1e, n2s, n2e = *node1.lines, *node2.lines
            return (
                (n1s == n2s or n1e == n2e)
                or (n1s < n2s and n1e > n2s)
                or (n1s < n2e and n1e > n2e)
            )

        from_buffer = deepcopy(self._data[from_name])
        to_buffer = deepcopy(self._data[to_name])
        buffer = []

        from_idx = 0
        to_idx = 0
        while from_idx < len(from_buffer) and to_idx < len(to_buffer):
            next_from, next_to = from_buffer[from_idx], to_buffer[to_idx]
            if overlap(next_from, next_to):
                if next_from.symbol == qt_symbol:
                    buffer.append(next_from)
                    to_idx += 1
                    from_idx += 1
                    while overlap(next_from, (next_to := to_buffer[to_idx])):
                        to_idx += 1
                else:
                    buffer.append(next_to)
                    to_idx += 1
                    from_idx += 1
                    while overlap((next_from := to_buffer[from_idx]), next_to):
                        from_idx += 1
            else:
                if next_from.lines[0] < next_to.lines[0]:
                    buffer.append(next_from)
                    from_idx += 1
                else:
                    buffer.append(next_to)
                    to_idx += 1

        self._data[to_name] = buffer


class Lexer(object):
    RULES_PATH: ClassVar[Path] = Path(__file__).parent / "base_lexer_rules.txt"

    def __init__(self):
        self._language = Language()
        self._rules = []
        self._special_rules = {}
        self._repo = LexerDataRepository()

        self._load_and_compile_rules(Lexer.RULES_PATH)
        self.register_special_rule(
            "PURGE-WHITESPACE", self._special_rule__purge_whitspace
        )

    def register_special_rule(self, name: str, callback: Callable[..., None]):
        self._special_rules[name] = callback

    def parse_file(self, path: Path) -> list[QuantizedASTNode]:
        buffer = []
        line = 1
        with open(path, "r") as infile:
            while char := infile.read(1):
                buffer.append(
                    QuantizedASTNode(
                        self._language.quantize_symbol(char), (line, line), char
                    )
                )
                if char == "\n":
                    line += 1
        self._repo.new_branch("master", buffer)

        self._run_rules()

        return self._repo.load("master")

    def _load_and_compile_rules(self, path: Path):
        for rule in load_rules(path):
            if isinstance(rule, SpecialRule):
                self._rules.append(rule)
            else:
                qt_rule = self._language.quantize_rule(rule)
                self._rules.append(
                    (qt_rule, ThompsonConstructor.construct_rule(qt_rule))
                )

    def _run_rules(self):
        for rule in self._rules:
            if isinstance(rule, SpecialRule):
                assert rule.symbol in self._special_rules
                self._special_rules[rule.symbol](rule)
            else:
                self._run_qt_rule(*rule)

    def _run_qt_rule(self, qt_rule: QuantizedRule, rule_graph: Graph):
        traveler = GraphTraveler(rule_graph)

        base_buffer = self._repo.load(qt_rule)
        buffer: list[QuantizedASTNode] = []
        processed = []
        finished_idx = -1
        finished_idx_buffer = -1
        idx = 0

        def add_rule_match(buff_idx):
            nonlocal processed
            inclusive_start, inclusive_end = qt_rule.options.inclusive
            if not inclusive_start:
                processed.append(buffer[0])

            rule_slice = slice(int(not inclusive_start), buff_idx + (inclusive_end))
            lines = (
                min([node.lines[0] for node in buffer[rule_slice]]),
                max([node.lines[1] for node in buffer[rule_slice]]),
            )
            processed.append(
                QuantizedASTNode(
                    qt_rule.symbol,
                    lines,
                    None,
                    buffer[rule_slice],
                )
            )

            if not inclusive_end:
                processed.append(buffer[buff_idx])

        while idx < len(base_buffer):
            node = base_buffer[idx]
            traveler.step(node.symbol)
            buffer.append(node)

            if traveler.valid_so_far():
                if traveler.is_finished():
                    finished_idx = idx
                    finished_idx_buffer = len(buffer) - 1
                idx += 1
            else:
                if finished_idx >= 0:
                    add_rule_match(finished_idx_buffer)
                    idx = finished_idx + 1
                    finished_idx = -1
                    finished_idx_buffer = -1
                else:
                    processed.append(buffer[0])
                    idx = idx + 2 - len(buffer)
                buffer.clear()
                traveler.reset()

        if finished_idx >= 0:
            add_rule_match(finished_idx_buffer)
            processed.extend(base_buffer[finished_idx + 1 :])
        else:
            processed.extend(buffer)

        self._repo.save(qt_rule, processed)

    def _special_rule__purge_whitspace(self, rule: SpecialRule):
        qt_whitespace = self._language.quantize_symbol("WHITESPACE")
        qt_linebreak = self._language.quantize_symbol("LINEBREAK")
        buffer = self._repo.load(rule)
        buffer = [t for t in buffer if t.symbol not in [qt_whitespace, qt_linebreak]]
        self._repo.save(rule, buffer)

    def _utility__find_groups(
        self,
        rule: Rule,
        start_sym: str,
        end_sym: Optional[str] = None,
        is_end_func: Optional[
            Callable[[int, dict, Language], tuple[bool, dict]]
        ] = None,
    ) -> list[tuple[int, int]]:
        """
        INCLUSIVE
        """
        qt_start_sym = self._language.quantize_symbol(start_sym)
        qt_end_sym = (
            None if end_sym is None else self._language.quantize_symbol(end_sym)
        )

        state: dict = {}

        def is_end(symbol: int) -> bool:
            nonlocal state
            if end_sym is not None:
                return symbol == qt_end_sym
            else:
                assert is_end_func is not None
                result, state = is_end_func(symbol, state, self._language)
                return result

        groupings = []
        start_idx = -1

        for idx, node in enumerate(self._repo.load(rule)):
            if node.symbol == qt_start_sym:
                start_idx = idx
            elif start_idx >= 0 and is_end(node.symbol):
                groupings.append((start_idx, idx))
                start_idx = -1

        return groupings

    def _utility__consolidate_groups(
        self,
        rule: Rule,
        groups: list[tuple[int, int]],
        sym_name: str,
        inclusive: tuple[bool, bool] = (True, True),
    ):
        qt_sym = self._language.quantize_symbol(sym_name)

        last_idx = 0
        processed = []
        buffer = self._repo.load(rule)

        for s, e in groups:
            # Inclusivity
            s = s if inclusive[0] else s + 1
            e = e if inclusive[1] else e - 1

            processed.extend(buffer[last_idx:s])
            if s <= e:
                rule_slice = slice(s, e + 1)
                lines = (
                    min([node.lines[0] for node in buffer[rule_slice]]),
                    max([node.lines[1] for node in buffer[rule_slice]]),
                )
                processed.append(
                    QuantizedASTNode(
                        qt_sym,
                        lines,
                        (
                            "".join([node.serialize("") for node in buffer[rule_slice]])
                        ).strip(),
                    )
                )
                last_idx = e + 1
        processed.extend(buffer[last_idx:])
        self._repo.save(rule, processed)
