from enum import Enum
from pathlib import Path
import re
import json
from copy import copy

"""
Rules
"""


class TokenDefinitions(object):
    PATH = Path(__file__).parent / "tokens.json"

    def __init__(self):
        with open(TokenDefinitions.PATH, "r") as infile:
            loaded_tok_defs = json.load(infile)
            self.tok_defs = loaded_tok_defs["tokens"]
            self.keywords = loaded_tok_defs["keywords"]
        self.name_to_tok_defs_idx = {
            tok_def["name"]: i for i, tok_def in enumerate(self.tok_defs)
        }
        self.all_possible_tokens = [tok_def["name"] for tok_def in self.tok_defs]

    def is_tok_valid_so_far(self, tok_name: str, s: str) -> bool:
        assert tok_name in self.name_to_tok_defs_idx
        idx = self.name_to_tok_defs_idx[tok_name]
        rule = self.tok_defs[idx][
            (
                "pattern_so_far"
                if "pattern_so_far" in self.tok_defs[idx].keys()
                else "pattern"
            )
        ]
        return self._rule_satisfied(s, rule)

    def is_tok_valid(self, tok_name: str, s: str) -> bool:
        assert tok_name in self.name_to_tok_defs_idx
        idx = self.name_to_tok_defs_idx[tok_name]
        rule = self.tok_defs[idx]["pattern"]
        return self._rule_satisfied(s, rule)

    def _rule_satisfied(self, s: str, rule: str) -> bool:
        match = re.match(rule, s)
        if match is None:
            return False
        return match.span() == (0, len(s))


"""
Tokens
"""


class Token(object):
    def __init__(self, tok_name: str, value: str):
        self.tok_name = tok_name
        self.value = value

    def __repr__(self) -> str:
        return f"{self.tok_name}: {self.value}"


"""
Backus-Naur Form
"""


class BNFTracker(object):
    class BNFTrackerState(Enum):
        NONE = 0
        MULTIPLE = 1
        UNIQUE = 2

    def __init__(self, tok_defs: TokenDefinitions):
        self.started = False
        self.possible: list[str] = []
        self.buffer = ""
        self.failed_buffer = ""
        self.tok_defs = tok_defs

    @property
    def state(self) -> BNFTrackerState:
        if not self.started:
            return BNFTracker.BNFTrackerState.NONE

        match len(self.possible):
            case 0:
                return BNFTracker.BNFTrackerState.NONE
            case 1:
                return BNFTracker.BNFTrackerState.UNIQUE
            case _:
                return BNFTracker.BNFTrackerState.MULTIPLE

    @property
    def is_unique(self) -> bool:
        return self.state == BNFTracker.BNFTrackerState.UNIQUE

    def add_next_char_if_valid(self, char: str) -> bool:
        assert len(char) == 1

        # Initialize
        if not self.started:
            self.possible = copy(self.tok_defs.all_possible_tokens)
            self.started = True

        # Filter for still applicable tokens
        appended_buffer = self.buffer + char
        filtered = []
        for tok_name in self.possible:
            if self.tok_defs.is_tok_valid_so_far(tok_name, appended_buffer):
                filtered.append(tok_name)

        # Update state
        if len(filtered):
            self.possible = filtered
            self.buffer = appended_buffer
            return True
        else:
            self.failed_buffer += char
            return False

    def get_tok(self, reset: bool = True) -> Token:
        def resolve_name_token(token: Token):
            for keyword in self.tok_defs.keywords:
                if keyword == token.value:
                    return Token(keyword, token.value)
            return token

        if len(self.buffer) and self.state == BNFTracker.BNFTrackerState.UNIQUE:
            if self.tok_defs.is_tok_valid(self.possible[0], self.buffer):
                assert len(self.possible) == 1
                token = Token(self.possible[0], self.buffer)
                if token.tok_name == "name":
                    token = resolve_name_token(token)
                if reset:
                    self.reset()
                return token

        failed = self.failed_buffer
        if reset:
            self.reset()
        return Token("unknown", failed)

    def reset(self):
        self.possible.clear()
        self.buffer = ""
        self.failed_buffer = ""
        self.started = False


"""
Lexical Parser
"""


class LexicalParser(object):
    def __init__(self):
        self.tokens = []
        self.tracker = BNFTracker(TokenDefinitions())

    def next(self, char: str):
        if not self.tracker.add_next_char_if_valid(char):
            if (next_tok := self.tracker.get_tok()).tok_name not in [
                "unknown",
                "whitespace",
            ]:
                self.tokens.append(next_tok)
            self.tracker.add_next_char_if_valid(char)

    def parse_file(self, path: Path):
        with open(path, "r") as infile:
            while nxt_chr := infile.read(1):
                self.next(nxt_chr)

    def save_tokens(self, path: Path):
        with open(path, "w") as outfile:
            for token in self.tokens:
                outfile.write(f"{token}\n")


"""
Driver
"""

if __name__ == "__main__":
    PROJ_DIR = Path(__file__).parent.parent.parent.parent
    OUTPUT_PATH = PROJ_DIR / "output" / "lexen.txt"
    SAMPLE_PATH = PROJ_DIR / "sample" / "struct_defs.c"
    # SAMPLE_PATH = PROJ_DIR / "sample" / "libgit2" / "src" / "libgit2" / "apply.c"

    lexy = LexicalParser()
    lexy.parse_file(SAMPLE_PATH)
    lexy.save_tokens(OUTPUT_PATH)
