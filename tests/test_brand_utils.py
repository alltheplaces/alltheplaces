from locations.brand_utils import extract_located_in


def test_extract_located_in_contains_mode():
    """Test default 'contains' mode matching."""
    mappings = [
        (["7-11", "7-ELEVEN"], {"brand": "7-Eleven", "brand_wikidata": "Q259340"}),
        (["LOTUS"], {"brand": "Lotus's", "brand_wikidata": "Q2647070"}),
    ]

    assert extract_located_in("ATM at 7-11 Store", mappings) == ("7-Eleven", "Q259340")
    assert extract_located_in("atm at 7-eleven", mappings) == ("7-Eleven", "Q259340")  # Case-insensitive
    assert extract_located_in("LOTUS MALL", mappings) == ("Lotus's", "Q2647070")
    assert extract_located_in("SHELL GAS STATION", mappings) == (None, None)
    assert extract_located_in("", mappings) == (None, None)


def test_extract_located_in_word_boundaries():
    """Test word boundary matching to avoid false positives."""
    mappings = [
        (["PTT"], {"brand": "PTT", "brand_wikidata": "Q1505539"}),
        (["TOPS"], {"brand": "Tops", "brand_wikidata": "Q7825140"}),
    ]

    # Should match with word boundaries
    assert extract_located_in("PTT", mappings) == ("PTT", "Q1505539")
    assert extract_located_in("PTT STATION", mappings) == ("PTT", "Q1505539")

    # Should NOT match when embedded in alphanumeric string
    assert extract_located_in("HTTPTTPS", mappings) == (None, None)


def test_extract_located_in_equals_mode():
    """Test 'equals' mode matching."""
    mappings = [
        (["PREMIER"], {"brand": "Premier", "brand_wikidata": "Q7240340"}, "equals"),
    ]

    assert extract_located_in("PREMIER", mappings) == ("Premier", "Q7240340")
    assert extract_located_in("WALLSEND PREMIER", mappings) == (None, None)


def test_extract_located_in_mixed_modes():
    """Test overridden match mode by mappings"""
    mappings = [
        (["PREMIER"], {"brand": "Premier", "brand_wikidata": "Q7240340"}, "equals"),
    ]

    assert extract_located_in("Premier", mappings, match_mode="contains") == ("Premier", "Q7240340")
    assert extract_located_in("WALLSEND PREMIER", mappings, match_mode="contains") == (None, None)


def test_extract_located_in_thai_examples():
    """Test Thai Unicode character handling."""
    mappings = [
        (["โลตัส", "LOTUS"], {"brand": "Lotus's", "brand_wikidata": "Q2647070"}),
        (["ปตท", "PTT"], {"brand": "PTT", "brand_wikidata": "Q1505539"}),
        (["ท็อปส์", "TOPS"], {"brand": "Tops", "brand_wikidata": "Q7825140"}),
        (["แฟมิลี่มาร์ท", "FAMILY MART"], {"brand": "FamilyMart", "brand_wikidata": "Q1396171"}),
    ]

    assert extract_located_in("ATM โลตัส สาขา 123", mappings) == ("Lotus's", "Q2647070")
    assert extract_located_in("สถานีบริการน้ำมัน ปตท", mappings) == ("PTT", "Q1505539")
    assert extract_located_in("ท็อปส์ มาร์เก็ต", mappings) == ("Tops", "Q7825140")

    assert extract_located_in("ทีเอ็มบีธนชาตTOPS DAILY", mappings) == ("Tops", "Q7825140")


def test_extract_located_in_special_characters():
    """Test handling of special characters in keywords."""
    # Multiple keywords with special character variations
    mappings = [
        (["CJ EXPRESS", "CJ. EXPRESS"], {"brand": "CJ Express", "brand_wikidata": "Q125874457"}),
    ]
    assert extract_located_in("CJ EXPRESS", mappings) == ("CJ Express", "Q125874457")
    assert extract_located_in("CJ. EXPRESS", mappings) == ("CJ Express", "Q125874457")

    # Special characters are part of the pattern
    mappings = [
        (["7-11"], {"brand": "7-Eleven", "brand_wikidata": "Q259340"}),
        (["CJ. EXPRESS"], {"brand": "CJ Express", "brand_wikidata": "Q125874457"}),
    ]
    assert extract_located_in("7-11", mappings) == ("7-Eleven", "Q259340")
    assert extract_located_in("CJ. EXPRESS", mappings) == ("CJ Express", "Q125874457")

    # Should not match partial patterns
    assert extract_located_in("7011", mappings) == (None, None)
    assert extract_located_in("CJ EXPRESS", mappings) == (None, None)  # Dot is required


def test_extract_located_in_brand_vs_name():
    """Test that function handles both 'brand' and 'name' keys."""
    mappings_with_brand = [
        (["TEST"], {"brand": "Test Brand", "brand_wikidata": "Q123"}),
    ]
    mappings_with_name = [
        (["TEST"], {"name": "Test Name", "brand_wikidata": "Q456"}),
    ]

    # Should prefer 'brand' key
    assert extract_located_in("TEST", mappings_with_brand) == ("Test Brand", "Q123")

    # Should fallback to 'name' key
    assert extract_located_in("TEST", mappings_with_name) == ("Test Name", "Q456")


def test_extract_located_in_missing_brand():
    """Test that function handles a missing brand key."""
    mappings = [
        (["TEST"], {"brand_wikidata": "Q123"}),
    ]

    assert extract_located_in("TEST", mappings) == (None, "Q123")


def test_extract_located_in_first_match_wins():
    """Test that first matching mapping wins."""
    mappings = [
        (["STORE"], {"brand": "Store A", "brand_wikidata": "Q1"}),
        (["STORE"], {"brand": "Store B", "brand_wikidata": "Q2"}),
    ]

    # First match should win
    assert extract_located_in("STORE", mappings) == ("Store A", "Q1")


def test_extract_located_in_whitespace_handling():
    """Test that whitespace is properly handled."""
    mappings = [
        (["LOTUS"], {"brand": "Lotus's", "brand_wikidata": "Q2647070"}),
    ]

    assert extract_located_in("  LOTUS  ", mappings) == ("Lotus's", "Q2647070")
    assert extract_located_in("\tLOTUS\n", mappings) == ("Lotus's", "Q2647070")