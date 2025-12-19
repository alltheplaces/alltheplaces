import json
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address


class ESunBankTWSpider(JSONBlobSpider):
    name = "e_sun_bank_tw"
    item_attributes = {"brand": "玉山商業銀行", "brand_wikidata": "Q5321663"}
    start_urls = [
        "https://www.esunbank.com/en/about/locations/branch",
        "https://www.esunbank.com/en/about/locations/atm",
    ]
    no_refs = True

    def extract_json(self, response: Response) -> dict | list[dict]:
        json_data = json.loads(
            response.xpath('//*[contains(text(),"var info")]/text()').re_first(r"var info\s*=\s*(\[.*\])\s*;")
        )
        return json_data

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "branch" in response.url:
            item["addr_full"] = clean_address(feature["EDeptAddress"])
            item["name"] = feature["EDept"]
            apply_category(Categories.BANK, item)
        elif "atm" in response.url:
            item["street"] = feature["Location"]
            item["name"] = "-".join(["玉山商業銀行", "ATM"])
            apply_category(Categories.ATM, item)
        yield item
