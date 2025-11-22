from dataclasses import dataclass
from pathlib import Path
from time import time

from olive.parse.regex.graph import GraphTraveler
from olive.parse.regex.language import Language
from olive.parse.regex.rules import RawRule
from olive.parse.regex.thompson import ThompsonConstructor

"""
Lexical Parser
"""


@dataclass
class Token(object):
    qt_sym: int
    raw_value: str


class LexicalParser(object):
    def __init__(self, rules_path: Path):
        self._language = Language()
        self._constructor = ThompsonConstructor()

        rule_cnt = 0
        for rule in RawRule.load(rules_path):
            rule_cnt += 1
            qt_rule = self._language.quantize_rule(rule)
            self._constructor.construct_rule(qt_rule)

        self._traveler = GraphTraveler(self._constructor._graph, rule_cnt)
        self._tokens: list[Token] = []
        self._buffer = ""

    def next(self, char: str):
        qt_char = self._language.quantize_symbol(char)
        self._traveler.step(qt_char)
        self._buffer += char

        if not self._traveler.valid_so_far():
            self._traveler.revert_step()
            self._buffer = self._buffer[:-1]
            self._save_current_match()
            self._traveler.step(qt_char)
            self._buffer += char

    def _save_current_match(self):
        final_state = self._traveler.reached_symbols()
        if final_state is not None:
            self._tokens.append(Token(final_state, self._buffer))
        self._traveler.reset()
        self._buffer = ""

    def parse_file(self, path: Path):
        with open(path, "r") as infile:
            while nxt_chr := infile.read(1):
                self.next(nxt_chr)
            self._save_current_match()

    def save_tokens(self, path: Path):
        with open(path, "w") as outfile:
            for token in self._tokens:
                outfile.write(
                    f"{self._language.dequantize_symbol(token.qt_sym)}: {token.raw_value}\n"
                )


"""
Driver
"""

if __name__ == "__main__":
    start = time()
    RULES_PATH = Path(__file__).parent / "rules.txt"
    OUTPUT_PATH = Path(__file__).parent / "lexen.txt"
    SAMPLE_PATH = Path(__file__).parent / "apply.c"

    lexy = LexicalParser(RULES_PATH)
    lexy.parse_file(SAMPLE_PATH)
    lexy.save_tokens(OUTPUT_PATH)
    end = time()

    print(f"Duration: {end - start:.2f} Seconds")
