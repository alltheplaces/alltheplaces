import json
import re
from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class Tog24GBSpider(JSONBlobSpider):
    name = "tog24_gb"
    item_attributes = {"brand": "TOG24", "brand_wikidata": "Q131273719"}
    start_urls = ["https://www.tog24.com/apps/store-locator"]

    def extract_json(self, response: Response) -> list:
        return [
            json.loads(store)
            for store in re.findall(
                r"markersCoords.push\(({\".+?)\);",
                response.xpath('//script[contains(text(),"markersCoords")]/text()').get(""),
            )
        ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        store_info = Selector(text=item.pop("addr_full"))
        item["branch"] = store_info.xpath('//*[@class="name"]/text()').get("").replace("TOG24", "").strip()
        item["addr_full"] = clean_address(store_info.xpath('//*[contains(@class, "address")]/text()').getall())
        item["phone"] = store_info.xpath('//*[@class="phone"]/text()').get()
        item["email"] = store_info.xpath('//*[@class="email"]/text()').get()
        if "Stockist" not in item["branch"]:
            yield item
