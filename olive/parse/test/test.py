from olive.parse.struct.description import description_from_ast
from olive.parse.struct.struct_lexer import StructLexer
from olive.parse.lexer.ast import RawASTNode
from pathlib import Path


TESTS = [
    "test__variable_description.txt",
    "test__union_description.txt",
    "test__struct_description.txt",
    "test__typedef_ref_description.txt",
]


def run_test_cases(test_file: Path):
    lexy = StructLexer()
    results_quantized = lexy.parse_file(test_file)
    results = [
        RawASTNode.resolve_quantized_ast_tree(result, lexy._language)
        for result in results_quantized
    ]
    descriptions = []
    for res in results:
        desc = description_from_ast(res)
        if desc is None:
            continue
        elif isinstance(desc, list):
            descriptions.extend(desc)
        else:
            descriptions.append(desc)

    out_dir = test_file.parent.parent / "out"
    out_file = out_dir / f"{test_file.stem}.out.txt"
    with open(out_file, "w") as ofile:
        for description in descriptions:
            ofile.write(description.serialize() + "\n\n")

    out_lex_file = out_dir / f"{test_file.stem}.lex.out.txt"
    with open(test_file, "r") as expect_file:
        with open(out_file, "r") as actual_file:
            for idx, (exp_line, act_line) in enumerate(
                zip(expect_file.readlines(), actual_file.readlines())
            ):
                if exp_line.strip() != act_line.strip():
                    print(
                        f"TEST FAILURE FOR {test_file.stem}\n"
                        + f"Line: {idx + 1}\n"
                        + "Expected:\n"
                        + exp_line
                        + "\nActual:\n"
                        + act_line
                    )
                    with open(out_lex_file, "w") as ofile:
                        for res in results:
                            ofile.write(res.serialize_graph() + "\n\n")


if __name__ == "__main__":
    test_dir = Path(__file__).parent / "cases"
    for filename in TESTS:
        run_test_cases(test_dir / filename)
