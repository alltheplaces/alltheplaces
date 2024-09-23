from locations.name_suggestion_index import NSI


def test_nsi_lookup_wikidata():
    nsi = NSI()
    data = nsi.lookup_wikidata("Q38076")
    assert data["identities"]["facebook"] == "mcdonalds"


def test_iter_wikidata():
    nsi = NSI()
    found = False
    for k, v in nsi.iter_wikidata("mcdonalds"):
        if k == "Q38076":
            found = True
    assert found


def test_iter_wikidata_all():
    for k, v in NSI().iter_wikidata():
        if k == "Q38076":
            break
    else:
        assert False


def test_normalise_label():
    # Diacritics are replaced with their closest ASCII equivalent.
    assert NSI.normalise_label("McDónalds") == "mcdonalds"
    # Ampersand characters are replaced with the word "and".
    assert NSI.normalise_label("McDonald, McDonald & McDonald") == "mcdonaldmcdonaldandmcdonald"
    # Punctuation (including spaces but excluding ampersands) are removed.
    assert NSI.normalise_label("Mac Donald") == "macdonald"
    # The label is converted to lower case.
    assert NSI.normalise_label("McDonalds") == "mcdonalds"


def test_iter_nsi():
    nsi = NSI()
    # McDonald's has identities in a number of locationSet's (countries)
    matches = list(nsi.iter_nsi("Q38076"))
    assert len(matches) > 4
    # Greggs is present only in the UK, only one match then
    matches = list(nsi.iter_nsi("Q3403981"))
    assert len(matches) == 1
    i = matches[0]
    assert i["displayName"] == "Greggs"
    assert i["tags"]["amenity"] == "fast_food"
