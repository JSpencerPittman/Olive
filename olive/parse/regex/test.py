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
    language: Language,
    gt: GraphTraveler,
    test_symbol: str,
    test_cases: list[tuple[str, bool]],
):
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


def test_concat(language: Language, gt: GraphTraveler):
    TEST_SYMBOL = "TEST_CONCAT"
    TEST_CASES = [("ABC", True), ("A", False), ("ABCA", False)]

    run_test_cases(language, gt, TEST_SYMBOL, TEST_CASES)


def test_quantifier_any(language: Language, gt: GraphTraveler):
    TEST_SYMBOL = "TEST_QUANTIFIER_ANY"
    TEST_CASES = [
        ("ABC", True),
        ("A", False),
        ("ABCA", False),
        ("ABCABC", True),
        ("ABCABCA", False),
        ("", True),
    ]

    run_test_cases(language, gt, TEST_SYMBOL, TEST_CASES)


def test_quantifier_optional(language: Language, gt: GraphTraveler):
    TEST_SYMBOL = "TEST_QUANTIFIER_OPTIONAL"
    TEST_CASES = [
        ("ABC", True),
        ("A", False),
        ("ABCA", False),
        ("ABCABC", False),
        ("", True),
    ]

    run_test_cases(language, gt, TEST_SYMBOL, TEST_CASES)


def test_quantifier_at_least_one(language: Language, gt: GraphTraveler):
    TEST_SYMBOL = "TEST_QUANTIFIER_AT_LEAST_ONE"
    TEST_CASES = [
        ("ABC", True),
        ("A", False),
        ("ABCA", False),
        ("ABCABC", True),
        ("", False),
    ]

    run_test_cases(language, gt, TEST_SYMBOL, TEST_CASES)


def test_comparison_or(language: Language, gt: GraphTraveler):
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

    run_test_cases(language, gt, TEST_SYMBOL, TEST_CASES)


def test_comparison_nested(language: Language, gt: GraphTraveler):
    TEST_SYMBOL = "TEST_QUANTIFIER_NESTED"
    TEST_CASES = [
        ("AC", True),
        ("ACB", False),
        ("B", True),
        ("ACACACCCCCCC", True),
        ("", True),
    ]

    run_test_cases(language, gt, TEST_SYMBOL, TEST_CASES)


def test_all_rules():
    rules_path = Path(__file__).parent / "test_rules.txt"
    raw_rules = RawRule.load(rules_path)
    language = Language()

    tests = [
        test_concat,
        test_quantifier_any,
        test_quantifier_optional,
        test_quantifier_at_least_one,
        test_comparison_or,
        test_comparison_nested,
    ]

    for raw_rule, test in zip(raw_rules, tests):
        qt_rule = language.quantize_rule(raw_rule)
        rg, _ = ThompsonConstructor.construct_rule(qt_rule)
        gt = GraphTraveler(rg)

        test(language, gt)


def test_single_case(tst_sym: str, expr: str, res: bool, rule_idx: int):
    rules_path = Path(__file__).parent / "test_rules.txt"
    raw_rules = RawRule.load(rules_path)
    language = Language()

    qt_rule = language.quantize_rule(raw_rules[rule_idx])
    rg, _ = ThompsonConstructor.construct_rule(qt_rule)
    gt = GraphTraveler(rg)

    run_test_cases(language, gt, tst_sym, [(expr, res)])


if __name__ == "__main__":
    test_all_rules()
