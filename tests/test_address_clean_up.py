from locations.pipelines.address_clean_up import clean_address, merge_address_lines


def test_merge_null_lines():
    assert merge_address_lines(["Suit 2", "555 High Street"]) == "Suit 2, 555 High Street"
    # Blank lines should be dropped
    assert merge_address_lines(["Suit 2", "", "555 High Street"]) == "Suit 2, 555 High Street"
    # None should be dropped
    assert merge_address_lines(["Suit 2", None, "555 High Street"]) == "Suit 2, 555 High Street"
    # Both should be
    assert merge_address_lines(["Suit 2", None, "555 High Street", "", None, ""]) == "Suit 2, 555 High Street"


def test_clean_address_null_lines():
    assert clean_address(["Suit 2", "555 High Street"]) == "Suit 2, 555 High Street"
    # Blank lines should be dropped
    assert clean_address(["Suit 2", "", "555 High Street"]) == "Suit 2, 555 High Street"
    # None should be dropped
    assert clean_address(["Suit 2", None, "555 High Street"]) == "Suit 2, 555 High Street"
    # Both should be
    assert clean_address(["Suit 2", None, "555 High Street", "", None, ""]) == "Suit 2, 555 High Street"


def test_clean_address_strip():
    # Leading and trailing spaces and new lines should be dropped
    assert clean_address([" Suit 2 ", "\n555 High Street\n"]) == "Suit 2, 555 High Street"
    # New lines inside a given line should be separated by ", "
    assert clean_address(["Suit 2\n555 High Street", "My Town"]) == "Suit 2, 555 High Street, My Town"
    # Also when there is only 1 line
    assert clean_address("Suit 2\n555 High Street, My Town") == "Suit 2, 555 High Street, My Town"
    # Trash lines should be dropped
    assert clean_address(["Suit 2", "  \t   ", "555 High Street"]) == "Suit 2, 555 High Street"
    # We should account for "weird" chars
    assert (
        clean_address("Suit 2\n 555 High Street\t My Town\n\r My Country")
        == "Suit 2, 555 High Street, My Town, My Country"
    )


def test_remove_undefined():
    assert clean_address("undefined") == ""
    assert clean_address("Undefined") == ""
    assert clean_address("UNDEFINED") == ""
    assert clean_address(" undefined") == ""
