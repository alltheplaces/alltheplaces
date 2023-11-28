from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class DirtCheapUSSpider(AgileStoreLocatorSpider):
    name = "dirt_cheap_us"
    item_attributes = {"brand": "Dirt Cheap", "brand_wikidata": "Q123013019"}
    allowed_domains = ["ilovedirtcheap.com"]

    def parse_item(self, item, location):
        item["website"] = "https://ilovedirtcheap.com/locations/store-details/" + location["slug"]
        item["image"] = location.get("storephoto")
        yield item
