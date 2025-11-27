from olive.file.file import CharacterNode


def test_basic_tree():
    root = CharacterNode({})
    root.add_string("apple")
    root.add_string("banana")
    root.add_string("cucumber")

    assert root.gather_first_n_matches("", 5) == ["apple", "banana", "cucumber"]
    assert root.gather_first_n_matches("apple", 1) == ["apple"]


def test_overlapping_tree():
    root = CharacterNode({})
    root.add_string("apple")
    root.add_string("apples")
    root.add_string("bananas")
    root.add_string("banana")

    assert root.gather_first_n_matches("apple", 3) == ["apple", "apples"]
    assert root.gather_first_n_matches("banana", 3) == ["banana", "bananas"]


if __name__ == "__main__":
    test_basic_tree()
    test_overlapping_tree()
