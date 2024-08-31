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


def test_generate_keys_from_nsi_attributes():
    nsi = NSI()
    matches = list(nsi.iter_nsi("Q38076"))
    keys_to_find = [
        ("mcdonalds", "McdonaldsSpider"),
        ("mcdonalds_fr", "McdonaldsFRSpider"),
        ("mai_dang_lao_mcdonalds_hk_mo", "MaiDangLaoMcDonaldsHKMOSpider"),
    ]
    for match in matches:
        key, class_name = NSI.generate_keys_from_nsi_attributes(match)
        assert key and class_name
        for position, keys_found in enumerate(keys_to_find):
            if keys_found[0] == key and keys_found[1] == class_name:
                del keys_to_find[position]
    assert len(keys_to_find) == 0

    matches = list(nsi.iter_nsi("Q108312837"))
    assert len(matches) == 1
    key, class_name = NSI.generate_keys_from_nsi_attributes(matches[0])
    assert key == "go_games_and_toys_us"
    assert class_name == "GoGamesAndToysUSSpider"
