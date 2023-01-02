from locations.categories import Fuel, apply_yes_no
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
