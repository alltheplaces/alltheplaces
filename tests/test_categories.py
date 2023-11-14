from locations.categories import Categories, Clothes, Fuel, HealthcareSpecialities, apply_category, apply_yes_no, get_category_tags, apply_clothes, apply_healthcare_specialities
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
    except TypeError:
        # Expected
        pass


def test_shop_tag_sanity():
    for cat in Categories:
        if cat.name.startswith("SHOP_"):
            shop_name = cat.name.split("_", 1)[1].lower()
            assert cat.value.get("shop") == shop_name


def test_cuisine_multiple():
    item = Feature()
    apply_category({"cuisine": "coffee_shop"}, item)
    assert item["extras"]["cuisine"] == "coffee_shop"

    apply_category({"cuisine": "coffee_shop"}, item)
    apply_category({"cuisine": "coffee_shop"}, item)
    assert item["extras"]["cuisine"] == "coffee_shop"

    apply_category({"cuisine": "coffee_shop"}, item)
    apply_category({"cuisine": "pizza"}, item)
    assert item["extras"]["cuisine"] == "coffee_shop;pizza"


def test_shop_yes_category():
    item = Feature()
    apply_category(Categories.FUEL_STATION, item)

    assert get_category_tags(item) == Categories.FUEL_STATION.value

    # Consider shop=yes an attribute, when there are other categories
    apply_category({"shop": "yes"}, item)
    assert get_category_tags(item) == Categories.FUEL_STATION.value

    # But top level when there are no other categories
    item = Feature()
    apply_category({"shop": "yes"}, item)
    assert get_category_tags(item) == {"shop": "yes"}

def test_clothes():
    item = Feature()
    apply_clothes([Clothes.MEN.value, Clothes.WOMEN.value], item)
    assert get_category_tags(item) == {"clothes": "men;women"}

    apply_clothes([Clothes.CHILDREN.value], item)
    assert get_category_tags(item) == {"clothes": "children;men;women"}

    item = Feature()
    apply_clothes([Clothes.WOMEN.value], item)
    assert get_category_tags(item) == {"clothes": "women"}

    apply_clothes([Clothes.WOMEN.value], item)
    assert get_category_tags(item) == {"clothes": "women"}

def test_healthcare_specialities():
    item = Feature()
    apply_healthcare_specialities([HealthcareSpecialities.GENERAL.value, HealthcareSpecialities.SURGERY.value, HealthcareSpecialities.ORTHODONTICS.value], item)
    assert get_category_tags(item) == {"healthcare:speciality": "general;orthodontics;surgery"}

    apply_healthcare_specialities([HealthcareSpecialities.DERMATOLOGY.value, HealthcareSpecialities.NEUROLOGY.value], item)
    assert get_category_tags(item) == {"healthcare:speciality": "dermatology;general;neurology;orthodontics;surgery"}

    item = Feature()
    apply_healthcare_specialities([HealthcareSpecialities.OCCUPATIONAL.value], item)
    assert get_category_tags(item) == {"healthcare:speciality": "occupational"}

    apply_healthcare_specialities([HealthcareSpecialities.OCCUPATIONAL.value], item)
    assert get_category_tags(item) == {"healthcare:speciality": "occupational"}
