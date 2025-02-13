from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class DennerCHSpider(StructuredDataSpider):
    name = "denner_ch"
    item_attributes = {"brand": "Denner", "brand_wikidata": "Q379911"}
    start_urls = ["https://www.denner.ch/de/index.php?type=667&tx_dennerstores_storelocator%5Baction%5D=mapdata"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json().values():
            yield scrapy.Request(url=response.urljoin(store["uri"]), callback=self.parse_sd, meta={"list_entry": store})

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["name"] = response.meta["list_entry"]["name"]

        if response.meta["list_entry"]["name"] == "Denner Express":
            apply_category(Categories.SHOP_CONVENIENCE, item)
        else:
            apply_category(Categories.SHOP_SUPERMARKET, item)

        item["lat"] = response.xpath('//*[@id="storeLatitude"]/@value').get()
        item["lon"] = response.xpath('//*[@id="storeLongitude"]/@value').get()
        yield item
