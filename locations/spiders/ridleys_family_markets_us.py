from typing import AsyncIterator

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class RidleysFamilyMarketsUSSpider(Spider):
    name = "ridleys_family_markets_us"
    item_attributes = {"brand": "Ridley's Family Markets", "brand_wikidata": "Q7332999"}
    start_urls = ["https://shopridleys.com/wp-admin/admin-ajax.php?action=imm_sections_fresh_find_store_nonce_ajax"]

    def parse(self, response: Response) -> AsyncIterator[dict]:
        nonce = response.json().get("data").get("nonce")
        yield scrapy.FormRequest(
            url="https://shopridleys.com/wp-admin/admin-ajax.php",
            formdata={
                "action": "imm_sections_get_stores_ajax",
                "nonce": f"{nonce}",
                "all_store": "yes",
            },
            callback=self.parse_details,
        )

    def parse_details(self, response: Response) -> AsyncIterator[dict]:
        for location in response.json().get("data", {}).get("data", {}).get("message", []):
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["branch"] = location.get("DisplayName")
            apply_category(Categories.SHOP_SUPERMARKET, item)
            yield item
