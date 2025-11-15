from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

"""
Tokens
"""


class TokenTypes(Enum):
    UNKNOWN = "UNKNOWN"
    NAME = "NAME"
    INTEGER = "INTEGER"


class Token(ABC):
    def __init__(self, value: str):
        self.value = value

    @abstractmethod
    def __repr__(self) -> str: ...


class UnknownToken(Token):
    TYPE = TokenTypes.UNKNOWN

    def __repr__(self) -> str:
        return f"Unknown: '{self.value}'"


class NameToken(Token):
    TYPE = TokenTypes.NAME

    def __repr__(self) -> str:
        return f"Name: '{self.value}'"


class IntegerToken(Token):
    TYPE = TokenTypes.INTEGER

    def __repr__(self) -> str:
        return f"Integer: '{self.value}'"


Tokens = list[Token]

TOKEN_REGISTRY = {
    TokenTypes.UNKNOWN: UnknownToken,
    TokenTypes.NAME: NameToken,
    TokenTypes.INTEGER: IntegerToken,
}

"""
Backus-Naur Form
"""


class BNFDefinition(ABC):
    @staticmethod
    @abstractmethod
    def is_valid_so_far(s: str) -> bool: ...

    @staticmethod
    @abstractmethod
    def is_valid(s: str) -> bool: ...


class BNFNameDefinition(BNFDefinition):
    TYPE: TokenTypes = TokenTypes.NAME

    @staticmethod
    def is_valid_so_far(s: str) -> bool:
        if not s[0].isalpha():
            return False
        for char in s:
            if not char.isalnum() and char != "_":
                return False
        return True

    @staticmethod
    def is_valid(s: str) -> bool:
        return BNFNameDefinition.is_valid_so_far(s)


class BNFIntegerDefinition(BNFDefinition):
    TYPE: TokenTypes = TokenTypes.INTEGER

    @staticmethod
    def is_valid_so_far(s: str) -> bool:
        for char in s:
            if not char.isdigit():
                return False
        return True

    @staticmethod
    def is_valid(s: str) -> bool:
        return BNFNameDefinition.is_valid_so_far(s)


BNF_DEFS_REGISTRY = {
    TokenTypes.NAME: BNFNameDefinition,
    TokenTypes.INTEGER: BNFIntegerDefinition,
}


class BNFTracker(object):
    class BNFTrackerState(Enum):
        NONE = 0
        MULTIPLE = 1
        UNIQUE = 2

    def __init__(self):
        self.started = False
        self.possible = []
        self.buffer = ""
        self.failed_buffer = ""

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
            self.possible = [tok_type for tok_type in BNF_DEFS_REGISTRY.keys()]
            self.started = True

        # Filter for still applicable tokens
        appended_buffer = self.buffer + char
        filtered = []
        for tok_type in self.possible[::-1]:
            tok_def = BNF_DEFS_REGISTRY[tok_type]
            if tok_def.is_valid_so_far(appended_buffer):
                filtered.append(tok_type)

        # Update state
        if len(filtered):
            self.possible = filtered
            self.buffer = appended_buffer
            return True
        else:
            self.failed_buffer += char
            return False

    def get_tok(self, reset: bool = True) -> Token:
        if len(self.buffer) and self.state == BNFTracker.BNFTrackerState.UNIQUE:
            assert len(self.possible) == 1
            token = TOKEN_REGISTRY[self.possible[0]](self.buffer)
            if reset:
                self.reset()
            return token
        else:
            failed = self.failed_buffer
            if reset:
                self.reset()
            return TOKEN_REGISTRY[TokenTypes.UNKNOWN](failed)

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
        self.tracker = BNFTracker()

    def next(self, char: str):
        if not self.tracker.add_next_char_if_valid(char):
            self.tokens.append(self.tracker.get_tok())
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
    SAMPLE_PATH = PROJ_DIR / "sample" / "libgit2" / "src" / "libgit2" / "apply.c"

    lexy = LexicalParser()
    lexy.parse_file(SAMPLE_PATH)
    lexy.save_tokens(OUTPUT_PATH)
