from locations.items import Feature, set_closed
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class WahoosUSSpider(AgileStoreLocatorSpider):
    name = "wahoos_us"
    item_attributes = {"brand": "Wahoo's Fish Tacos", "brand_wikidata": "Q7959827"}
    start_urls = [
        "https://www.wahoos.com/wp-admin/admin-ajax.php?action=asl_load_stores&nonce=33daf6dd9c&load_all=1&layout=1"
    ]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        if "closed" in item["name"]:
            set_closed(item)
        if " (" in item["name"]:
            item["name"] = item["name"].split(" (")[0]
        yield item
