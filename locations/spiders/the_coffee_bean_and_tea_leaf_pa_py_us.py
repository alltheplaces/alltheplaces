from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext import YextSpider


class TheCoffeeBeanAndTeaLeafPAPYUSSpider(YextSpider):
    name = "the_coffee_bean_and_tea_leaf_pa_py_us"
    item_attributes = {
        "brand": "The Coffee Bean & Tea Leaf",
        "brand_wikidata": "Q1141384",
    }
    api_key = "09bd200ec78ce60b227daa552e11b788"
    api_version = "20210701"
    wanted_types = ["restaurant"]
    drop_attributes = ["twitter"]

    def parse_item(self, item, location):
        apply_yes_no(Extras.DRIVE_THROUGH, item, location.get("c_driveThru", False))
        item["extras"]["website:order"] = location.get("c_oloURL")
        if store_name := location.get("c_storeName"):
            item["branch"] = store_name.removeprefix("The Coffee Bean & Tea Leaf").strip()
        yield item
