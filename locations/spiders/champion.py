import json
import re

from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class ChampionSpider(AmastyStoreLocatorSpider):
    name = "champion"
    item_attributes = {"brand": "Champion", "brand_wikidata": "Q2948688"}
    start_urls = ["https://www.championstore.com/en_gb/stores"]

    def parse(self, response, **kwargs):
        yield from self.parse_items(json.loads(re.search(r"jsonLocations: ({.+}),", response.text).group(1))["items"])

    def parse_item(self, item, location, popup_html):
        item["addr_full"] = popup_html.xpath('//span[contains(@class, "amlocator-address")]/text()').get()
        yield item
