from olive.parse.lexer.lexical import Token
from pathlib import Path
from queue import Queue


class Symbol(object):
    def __init__(self, is_comp: bool, value: str):
        self.is_comp = is_comp
        self.value = value


class Rule(object):
    def __init__(self, symbol: Symbol, expression: list[Symbol]):
        self.symbol = symbol
        self.expression = expression


class Rules(object):
    PATH = Path(__file__).parent / "rules.txt"

    def __init__(self):
        def parse_line(line: str) -> Rule:
            parts = line.split(":=")
            assert len(parts) == 2
            raw_symbol, raw_expression = parts[0].strip(), parts[1].strip().split(" ")

            assert raw_symbol.isupper()
            symbol = Symbol(True, raw_symbol)
            expression = [Symbol(s.isupper(), s) for s in raw_expression]
            return Rule(symbol, expression)

        self.rules = {}
        with open(Rules.PATH, "r") as infile:
            for line in infile.readlines():
                if (parsed_rule := parse_line(line)) is not None:
                    self.rules[parsed_rule.symbol.value] = parsed_rule
