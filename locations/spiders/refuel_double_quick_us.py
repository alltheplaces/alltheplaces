from locations.categories import Categories
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class RefuelDoubleQuickUSSpider(AgileStoreLocatorSpider):
    name = "refuel_double_quick_us"
    item_attributes = {"extras": Categories.SHOP_CONVENIENCE.value}
    allowed_domains = ["www.refuelmarket.com"]

    def parse_item(self, item, location):
        if location["title"].startswith("Refuel "):
            item["brand"] = "Refuel"
            item["brand_wikidata"] = "Q124987140"
        elif location["title"].startswith("Double Quick "):
            item["brand"] = "Double Quick"
            item["brand_wikidata"] = "Q124987186"
        item["ref"] = location["title"].split(" ")[-1]
        yield item
