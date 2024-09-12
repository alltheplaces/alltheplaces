from locations.categories import Extras, apply_yes_no
from locations.storefinders.yext_search import YextSearchSpider


class MuggAndBeanZASpider(YextSearchSpider):
    name = "mugg_and_bean_za"
    item_attributes = {"brand": "Mugg & Bean", "brand_wikidata": "Q6932113"}
    host = "https://location.muggandbean.co.za"

    def parse_item(self, location, item):
        item["branch"] = location["profile"].get("geomodifier")
        apply_yes_no(Extras.DELIVERY, item, location["profile"].get("c_delivery"))
        item["extras"]["website:menu"] = location["profile"].get("menuUrl")
        if "c_muggAndBeanLocatorFilters" in location["profile"]:
            apply_yes_no(Extras.HALAL, item, "Halaal" in location["profile"]["c_muggAndBeanLocatorFilters"])
        yield item
