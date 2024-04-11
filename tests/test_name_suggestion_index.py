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


def test_get_by_id():
    nsi = NSI()

    # Invalid items should not return an NSI entry
    assert nsi.get_item("N/A") is None
    assert nsi.get_item(-1) is None

    valid_id = nsi.nsi_json["brands/amenity/fuel"]["items"][0]["id"]
    assert nsi.get_item(valid_id)["id"] == valid_id
