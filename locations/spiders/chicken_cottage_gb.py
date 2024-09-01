from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class ChickenCottageGBSpider(AgileStoreLocatorSpider):
    name = "chicken_cottage_gb"
    item_attributes = {"brand": "Chicken Cottage", "brand_wikidata": "Q5096233"}
    allowed_domains = ["chickencottage.com"]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        item["branch"] = item.pop("name").removeprefix("Chicken Cottage ")
        yield item
