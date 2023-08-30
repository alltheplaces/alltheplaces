from locations.categories import Categories, apply_category
from locations.storefinders.yext import YextSpider


class IndependentFinancialUSSpider(YextSpider):
    name = "independent_financial_us"
    item_attributes = {"brand": "Independent Financial", "brand_wikidata": "Q6016398"}
    api_key = "ee4600854cf5501c53831bf944472e57"
    wanted_types = ["location", "atm"]

    def parse_item(self, item, location):
        if location["meta"]["entityType"] == "location":
            apply_category(Categories.BANK, item)
            item["ref"] = location.get("c_branchCode", location["meta"].get("id"))
            item["name"] = " ".join(filter(None, [location.get("name"), location.get("geomodifier")]))
        elif location["meta"]["entityType"] == "atm":
            apply_category(Categories.ATM, item)
            item["name"] = location.get("geomodifier")
        item["website"] = location.get("c_pagesURL")
        item.pop("email", None)
        item["extras"].pop("contact:instagram", None)
        item.pop("twitter", None)
        item.pop("facebook", None)
        yield item
