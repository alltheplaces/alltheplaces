from locations.items import merge_items


def test_merge_two():
    item_en = {}
    item_en["ref"] = "1"
    item_en["name"] = "Shop"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["name"] = "Magasin"
    item_fr["extras"] = {}
    assert [item for item in merge_items({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en")][0] == {
        "ref": "1",
        "name": "Shop",
        "extras": {"name:en": "Shop", "name:fr": "Magasin"},
    }


def test_matching_value():
    item_en = {}
    item_en["ref"] = "1"
    item_en["postcode"] = "1234"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["postcode"] = "1234"
    item_fr["extras"] = {}
    assert [item for item in merge_items({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en")][0] == {
        "ref": "1",
        "postcode": "1234",
        "extras": {},
    }


def test_merge_three():
    item_en = {}
    item_en["ref"] = "1"
    item_en["name"] = "Shop"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["name"] = "Magasin"
    item_fr["extras"] = {}
    item_de = {}
    item_de["ref"] = "1"
    item_de["name"] = "Laden"
    item_de["extras"] = {}
    assert [item for item in merge_items({"en": {"1": item_en}, "fr": {"1": item_fr}, "de": {"1": item_de}}, "en")][
        0
    ] == {"ref": "1", "name": "Shop", "extras": {"name:en": "Shop", "name:fr": "Magasin", "name:de": "Laden"}}


def test_join_different_phones():
    item_en = {}
    item_en["ref"] = "1"
    item_en["phone"] = "+27 1234"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["phone"] = "+27 5678"
    item_fr["extras"] = {}
    assert [item for item in merge_items({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en")][0] == {
        "ref": "1",
        "phone": "+27 1234; +27 5678",
        "extras": {},
    }
