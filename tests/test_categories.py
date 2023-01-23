from locations.categories import Categories, Fuel, apply_yes_no
from locations.items import Feature


def test_apply_yes_no():
    item = Feature()
    apply_yes_no(Fuel.CNG, item, True)
    assert item["extras"][Fuel.CNG.value] == "yes"
    apply_yes_no("my_string", item, True)
    assert item["extras"]["my_string"] == "yes"
    item = Feature()
    apply_yes_no(Fuel.CNG, item, False)
    assert not item.get("extras")
    apply_yes_no(Fuel.CNG, item, False, apply_positive_only=False)
    assert item["extras"][Fuel.CNG.value] == "no"
    try:
        apply_yes_no({}, item, True)
        assert False
    except AttributeError:
        # Expected
        pass


def test_shop_tag_sanity():
    for cat in Categories:
        if cat.name.startswith("SHOP_"):
            shop_name = cat.name.split("_", 1)[1].lower()
            assert cat.value.get("shop") == shop_name
