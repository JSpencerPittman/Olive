from pathlib import Path
from typing import Callable, ClassVar, Optional

from olive.parse.regex.graph import GraphTraveler, Graph
from olive.parse.regex.language import Language
from olive.parse.regex.rules import SpecialRule, QuantizedRule, load_rules
from olive.parse.regex.thompson import ThompsonConstructor
from olive.parse.lexer.ast import QuantizedASTNode


class Lexer(object):
    RULES_PATH: ClassVar[Path] = Path(__file__).parent / "base_lexer_rules.txt"

    def __init__(self):
        self._language = Language()
        self._rules = []
        self._special_rules = {}
        self._data = []

        self._load_and_compile_rules(Lexer.RULES_PATH)
        self.register_special_rule(
            "PURGE-WHITESPACE", self._special_rule__purge_whitspace
        )

    def register_special_rule(self, name: str, callback: Callable[..., None]):
        self._special_rules[name] = callback

    def parse_file(self, path: Path) -> list[QuantizedASTNode]:
        with open(path, "r") as infile:
            while char := infile.read(1):
                self._data.append(
                    QuantizedASTNode(self._language.quantize_symbol(char), char)
                )

        self._run_rules()

        return self._data

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
                if len(rule.rule):
                    self._special_rules[rule.symbol](rule.rule)
                else:
                    self._special_rules[rule.symbol]()
                continue

            self._run_qt_rule(*rule)

    def _run_qt_rule(self, qt_rule: QuantizedRule, rule_graph: Graph):
        traveler = GraphTraveler(rule_graph)

        buffer = []
        processed = []
        finished_idx = -1
        finished_idx_buffer = -1
        idx = 0

        while idx < len(self._data):
            node = self._data[idx]
            traveler.step(node.symbol)
            buffer.append(node)

            if traveler.valid_so_far():
                if traveler.is_finished():
                    finished_idx = idx
                    finished_idx_buffer = len(buffer) - 1
                idx += 1
            else:
                if finished_idx >= 0:
                    processed.append(
                        QuantizedASTNode(
                            qt_rule.symbol, None, buffer[: finished_idx_buffer + 1]
                        )
                    )
                    idx = finished_idx + 1
                    finished_idx = -1
                    finished_idx_buffer = -1
                else:
                    processed.append(buffer[0])
                    idx = idx + 2 - len(buffer)
                buffer.clear()
                traveler.reset()

        if finished_idx >= 0:
            processed.append(
                QuantizedASTNode(
                    qt_rule.symbol, None, buffer[: finished_idx_buffer + 1]
                )
            )
            processed.extend(self._data[finished_idx + 1 :])
        else:
            processed.extend(buffer)

        self._data = processed

    def _special_rule__purge_whitspace(self):
        qt_whitespace = self._language.quantize_symbol("WHITESPACE")
        qt_linebreak = self._language.quantize_symbol("LINEBREAK")
        self._data = [
            t for t in self._data if t.symbol not in [qt_whitespace, qt_linebreak]
        ]

    def _utility__find_groups(
        self,
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

        for idx, node in enumerate(self._data):
            if node.symbol == qt_start_sym:
                start_idx = idx
            elif start_idx >= 0 and is_end(node.symbol):
                groupings.append((start_idx, idx))
                start_idx = -1

        return groupings

    def _utility__consolidate_groups(
        self,
        groups: list[tuple[int, int]],
        sym_name: str,
        inclusive: tuple[bool, bool] = (True, True),
    ):
        qt_sym = self._language.quantize_symbol(sym_name)

        last_idx = 0
        processed = []
        for s, e in groups:
            # Inclusivity
            s = s if inclusive[0] else s + 1
            e = e if inclusive[1] else e - 1

            processed.extend(self._data[last_idx:s])
            if s + 1 != e:
                processed.append(
                    QuantizedASTNode(
                        qt_sym,
                        (
                            "".join(
                                [node.serialize("") for node in self._data[s + 1 : e]]
                            )
                        ).strip(),
                    )
                )
                last_idx = e + 1
        processed.extend(self._data[last_idx:])
        self._data = processed
