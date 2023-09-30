import re

from locations.storefinders.storelocatorwidgets import StoreLocatorWidgetsSpider


class RamrajCottonINSpider(StoreLocatorWidgetsSpider):
    name = "ramraj_cotton_in"
    item_attributes = {"brand": "Ramraj Cotton", "brand_wikidata": "Q119161281"}
    key = "2b4c1b15c69f161d98d09c413f287c69"

    def parse_item(self, item, location):
        item["addr_full"] = re.sub(r"\s+", " ", item["addr_full"])
        yield item
