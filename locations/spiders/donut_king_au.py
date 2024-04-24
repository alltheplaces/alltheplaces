import re

from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class DonutKingAUSpider(WPStoreLocatorSpider):
    name = "donut_king_au"
    item_attributes = {"brand_wikidata": "Q5296921", "brand": "Donut King"}
    start_urls = ["https://www.donutking.com.au/wp/wp-admin/admin-ajax.php?action=store_search&autoload=1"]
    time_format = "%I:%M %p"

    def parse_item(self, item, location):
        if "CLOSED" in re.split(r"\W+", item.get("name", "").upper()):
            return
        if "CLOSED" in re.split(r"\W+", item.get("addr_full", "").upper()):
            return
        if "CLOSED" in re.split(r"\W+", item.get("street_address", "").upper()):
            return
        yield item
