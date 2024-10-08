from locations.storefinders.freshop import FreshopSpider


class FamilyFareUSSpider(FreshopSpider):
    name = "family_fare_us"
    item_attributes = {"brand": "Family Fare", "brand_wikidata": "Q19868045"}
    app_key = "family_fare"

    def parse_item(self, item, location):
        item["phone"] = item.get("phone", "").split("\n", 1)[0].strip()
        yield item
