import re
from json import loads
from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.amasty_store_locator import AmastyStoreLocatorSpider


class ChampionSpider(AmastyStoreLocatorSpider):
    name = "champion"
    item_attributes = {"brand": "Champion", "brand_wikidata": "Q2948688"}
    start_urls = ["https://www.championstore.com/en_gb/stores"]

    def parse(self, response: Response) -> Iterable[Feature]:
        yield from self.parse_features(loads(re.search(r"jsonLocations: ({.+}),", response.text).group(1))["items"])

    def post_process_item(self, item: Feature, feature: dict, popup_html: Selector) -> Iterable[Feature]:
        item["addr_full"] = popup_html.xpath('//span[contains(@class, "amlocator-address")]/text()').get()
        yield item
