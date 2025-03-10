import re

from locations.categories import Categories, Extras, apply_yes_no
from locations.storefinders.yext_answers import YextAnswersSpider


class TropicalSmoothieCafeUSSpider(YextAnswersSpider):
    name = "tropical_smoothie_cafe_us"
    item_attributes = {
        "brand": "Tropical Smoothie Cafe",
        "brand_wikidata": "Q7845817",
        "extras": Categories.FAST_FOOD.value,
    }
    api_key = "e00ed8254f827f6c73044941473bb9e9"
    experience_key = "answers"
    environment = "STAGING"
    feature_type = "restaurants"

    def parse_item(self, location, item):
        if email := location.get("c_franchiseeEmail"):
            item["email"] = re.sub(r"[;,].*", "", email)
        if amenities := location.get("c_locationPageServices"):
            apply_yes_no(Extras.WIFI, item, "Wifi" in amenities, False)
        yield item
