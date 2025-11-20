from olive.parse.regex.rules import RawRule
from olive.parse.regex.language import Language
from olive.parse.regex.thompson import ThompsonConstructor
from olive.parse.regex.graph import GraphTraveler
from pathlib import Path
from typing import Any


def assert_cond(condition: bool, msg: str, actual: Any, exp: Any):
    if not condition:
        print(f"FAILURE:{msg}\n\tActual: {actual}\n\tExpected: {exp}")
        assert False


def run_test_cases(
    test_symbol: str,
    test_cases: list[tuple[str, bool]],
    rules: list[str],
):
    language = Language()
    constructor = ThompsonConstructor()
    for rule in rules:
        symbol, terms = rule.split(":=")
        raw_rule = RawRule(
            symbol.strip(), [r.strip() for r in terms.strip().split(" ")]
        )
        qt_rule = language.quantize_rule(raw_rule)
        constructor.construct_rule(qt_rule)
    gt = GraphTraveler(constructor._graph)

    for tst_expr, tst_res in test_cases:
        gt.reset()

        for char in tst_expr:
            qt_char = language.quantize_symbol(char, True)
            assert qt_char is not None
            gt.step(qt_char)
        r = gt.reached_symbols()

        if tst_res:
            assert_cond(
                r is not None,
                f"Regex '{tst_expr}' was not matched.",
                r is not None,
                tst_res,
            )
            assert r is not None
            assert_cond(
                language.dequantize_symbol(r) == test_symbol,
                f"Test Symbol not matched by '{tst_expr}'.",
                language.dequantize_symbol(r),
                test_symbol,
            )
        else:
            assert_cond(
                r is None, f"Regex should not have matched: '{tst_expr}'", True, False
            )


def test_concat():
    TEST_SYMBOL = "TEST_CONCAT"
    TEST_CASES = [("ABC", True), ("A", False), ("ABCA", False)]
    RULES = ["TEST_CONCAT := A B C"]

    run_test_cases(TEST_SYMBOL, TEST_CASES, RULES)


def test_quantifier_any():
    TEST_SYMBOL = "TEST_QUANTIFIER_ANY"
    TEST_CASES = [
        ("ABC", True),
        ("A", False),
        ("ABCA", False),
        ("ABCABC", True),
        ("ABCABCA", False),
        ("", True),
    ]
    RULES = ["TEST_QUANTIFIER_ANY := ( A B C ) *"]

    run_test_cases(TEST_SYMBOL, TEST_CASES, RULES)


def test_quantifier_optional():
    TEST_SYMBOL = "TEST_QUANTIFIER_OPTIONAL"
    TEST_CASES = [
        ("ABC", True),
        ("A", False),
        ("ABCA", False),
        ("ABCABC", False),
        ("", True),
    ]
    RULES = ["TEST_QUANTIFIER_OPTIONAL := ( A B C ) ?"]

    run_test_cases(TEST_SYMBOL, TEST_CASES, RULES)


def test_quantifier_at_least_one():
    TEST_SYMBOL = "TEST_QUANTIFIER_AT_LEAST_ONE"
    TEST_CASES = [
        ("ABC", True),
        ("A", False),
        ("ABCA", False),
        ("ABCABC", True),
        ("", False),
    ]
    RULES = ["TEST_QUANTIFIER_AT_LEAST_ONE := ( A B C ) +"]

    run_test_cases(TEST_SYMBOL, TEST_CASES, RULES)


def test_comparison_or():
    TEST_SYMBOL = "TEST_COMPARISON_OR"
    TEST_CASES = [
        ("ABC", False),
        ("A", True),
        ("B", True),
        ("BC", False),
        ("C", True),
        ("ABCA", False),
        ("ABCABC", False),
        ("", False),
    ]
    RULES = ["TEST_COMPARISON_OR := ( A B C ) |"]

    run_test_cases(TEST_SYMBOL, TEST_CASES, RULES)


def test_comparison_nested():
    TEST_SYMBOL = "TEST_QUANTIFIER_NESTED"
    TEST_CASES = [
        ("AC", True),
        ("ACB", False),
        ("B", True),
        ("ACACACCCCCCC", True),
        ("", True),
    ]
    RULES = ["TEST_QUANTIFIER_NESTED := ( ( A C ) * B ) | ( C ) *"]

    run_test_cases(TEST_SYMBOL, TEST_CASES, RULES)


def test_symbol_reference():
    TEST_SYMBOL = "TEST_SYMBOL_REFERENCE"
    TEST_CASES = [
        ("ABCD", True),
        ("AD", False),
        ("ABCAD", False),
        ("ABCABCD", True),
        ("", False),
    ]
    RULES = ["TEST_CONCAT := A B C", "TEST_SYMBOL_REFERENCE := ( TEST_CONCAT ) + D"]

    run_test_cases(TEST_SYMBOL, TEST_CASES, RULES)


def test_all_rules():
    test_concat()
    test_quantifier_any()
    test_quantifier_optional()
    test_quantifier_at_least_one()
    test_comparison_or()
    test_comparison_nested()
    test_symbol_reference()


if __name__ == "__main__":
    test_all_rules()
