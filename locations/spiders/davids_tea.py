import json
import re
from typing import Iterable

from scrapy import Selector
from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class DavidsTeaSpider(JSONBlobSpider):
    name = "davids_tea"
    item_attributes = {"brand": "David's Tea", "brand_wikidata": "Q3019129"}
    start_urls = ["https://davidstea.com/apps/store-locator/"]

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
        item["branch"] = store_info.xpath('//*[@class="name"]/text()').get("").strip()
        item["street_address"] = clean_address(store_info.xpath('//*[contains(@class, "address")]/text()').getall())
        item["city"] = store_info.xpath('//*[@class="city"]/text()').get()
        item["state"] = store_info.xpath('//*[@class="prov_state"]/text()').get()
        item["postcode"] = store_info.xpath('//*[@class="postal_zip"]/text()').get()
        item["country"] = store_info.xpath('//*[@class="country"]/text()').get()
        item["website"] = response.url
        yield item
