from locations.items import merge_items


def return_first_merged(language_dict, main_language) -> dict:
    return [item for item in merge_items(language_dict, main_language)][0]


def test_merge_two():
    item_en = {}
    item_en["ref"] = "1"
    item_en["name"] = "Shop"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["name"] = "Magasin"
    item_fr["extras"] = {}
    assert return_first_merged({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en") == {
        "ref": "1",
        "name": "Shop",
        "extras": {"name:en": "Shop", "name:fr": "Magasin"},
    }


def test_same_value():
    item_en = {}
    item_en["ref"] = "1"
    item_en["postcode"] = "1234"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["postcode"] = "1234"
    item_fr["extras"] = {}
    assert return_first_merged({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en") == {
        "ref": "1",
        "postcode": "1234",
        "extras": {},
    }


def test_missing_value_main_language():
    item_en = {}
    item_en["ref"] = "1"
    item_en["branch"] = "Town"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["extras"] = {}
    assert return_first_merged({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en") == {
        "ref": "1",
        "branch": "Town",
        "extras": {
            "branch:en": "Town",
            "branch:fr": None,
        },
    }


def test_missing_value_other_language():
    item_en = {}
    item_en["ref"] = "1"
    item_en["branch"] = "Town"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["extras"] = {}
    assert return_first_merged({"en": {"1": item_en}, "fr": {"1": item_fr}}, "fr") == {
        "ref": "1",
        "extras": {
            "branch:fr": None,
            "branch:en": "Town",
        },
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
    assert return_first_merged({"en": {"1": item_en}, "fr": {"1": item_fr}, "de": {"1": item_de}}, "en") == {
        "ref": "1",
        "name": "Shop",
        "extras": {"name:en": "Shop", "name:fr": "Magasin", "name:de": "Laden"},
    }


def test_join_different_phones():
    item_en = {}
    item_en["ref"] = "1"
    item_en["phone"] = "+27 1234"
    item_en["extras"] = {}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["phone"] = "+27 5678"
    item_fr["extras"] = {}
    assert return_first_merged({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en") == {
        "ref": "1",
        "phone": "+27 1234; +27 5678",
        "extras": {},
    }


def test_no_match_yields_anyway_main_language():
    item_en = {}
    item_en["ref"] = "1"
    item_en["name"] = "Shop"
    item_en["extras"] = {}
    assert return_first_merged({"en": {"1": item_en}}, "en") == {"ref": "1", "name": "Shop", "extras": {}}


def test_no_match_yields_anyway_other_language():
    item_en = {}
    item_en["ref"] = "1"
    item_en["name"] = "Shop"
    item_en["extras"] = {}
    assert return_first_merged({"fr": {}, "en": {"1": item_en}}, "fr") == {"ref": "1", "name": "Shop", "extras": {}}


def test_translatable_extra():
    item_en = {}
    item_en["ref"] = "1"
    item_en["extras"] = {"alt_name": "Alty"}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["extras"] = {"alt_name": "Le Altie"}
    assert return_first_merged({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en") == {
        "ref": "1",
        "extras": {"alt_name": "Alty", "alt_name:en": "Alty", "alt_name:fr": "Le Altie"},
    }


def test_translatable_prefix():
    item_en = {}
    item_en["ref"] = "1"
    item_en["extras"] = {"website:menu": "example.com/en/menu"}
    item_fr = {}
    item_fr["ref"] = "1"
    item_fr["extras"] = {"website:menu": "example.com/fr/menu"}
    assert return_first_merged({"en": {"1": item_en}, "fr": {"1": item_fr}}, "en") == {
        "ref": "1",
        "extras": {
            "website:menu": "example.com/en/menu",
            "website:menu:en": "example.com/en/menu",
            "website:menu:fr": "example.com/fr/menu",
        },
    }
