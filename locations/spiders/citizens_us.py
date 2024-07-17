from locations.categories import Categories, apply_category
from locations.storefinders.yext import YextSpider


class CitizensUSSpider(YextSpider):
    name = "citizens_us"
    item_attributes = {"brand_wikidata": "Q5122694"}
    api_key = "d4d6be17717272573aeece729fdbec0c"
    wanted_types = ["location", "atm"]

    def parse_item(self, item, location):
        if not location.get("c_active", True):
            return
        if "BRANCH" in location.get("c_type", []):
            apply_category(Categories.BANK, item)
            item["ref"] = location.get("c_branchCode", location["meta"].get("id"))
            item["name"] = " ".join(filter(None, [location.get("name"), location.get("geomodifier")]))
        elif "ATM" in location.get("c_type", []):
            apply_category(Categories.ATM, item)
            item.pop("name", None)
        else:
            return
        item.pop("website", None)
        item["extras"].pop("contact:instagram", None)
        item.pop("twitter", None)
        item.pop("facebook", None)
        yield item
