import json
from typing import Iterable

from scrapy.http import Response

from locations.brand_utils import extract_located_in
from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.pipelines.address_clean_up import clean_address
from locations.spiders.carrefour_tw import CarrefourTWSpider
from locations.spiders.costco_au import COSTCO_SHARED_ATTRIBUTES
from locations.spiders.familymart_tw import FamilymartTWSpider
from locations.spiders.pxmart_tw import PxmartTWSpider
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class ESunBankTWSpider(JSONBlobSpider):
    name = "e_sun_bank_tw"
    item_attributes = {"brand": "玉山商業銀行", "brand_wikidata": "Q5321663"}
    start_urls = [
        "https://www.esunbank.com/en/about/locations/branch",
        "https://www.esunbank.com/en/about/locations/atm",
    ]
    no_refs = True

    LOCATED_IN_MAPPINGS = [
        (["家樂福", "CARREFOUR"], CarrefourTWSpider.brands["量販"]),
        (["全家", "FAMILYMART", "FAMILY"], FamilymartTWSpider.item_attributes),
        (["7-ELEVEN", "7-11", "統一超商"], SEVEN_ELEVEN_SHARED_ATTRIBUTES),
        (["萊爾富", "HI-LIFE", "HILIFE"], {"brand": "Hi-Life", "brand_wikidata": "Q11326216"}),
        (["OK MART"], {"brand": "OK Mart", "brand_wikidata": "Q10851968"}),
        (["全聯", "PX MART"], PxmartTWSpider.item_attributes),
        (["RT-MART"], {"brand": "RT-Mart", "brand_wikidata": "Q7277802"}),
        (["頂好", "WELLCOME"], {"brand": "Wellcome", "brand_wikidata": "Q706247"}),
        (["好市多", "COSTCO"], COSTCO_SHARED_ATTRIBUTES),
    ]

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
            # Extract retail brand from Location field for ATMs
            item["located_in"], item["located_in_wikidata"] = extract_located_in(
                feature.get("Location", ""), self.LOCATED_IN_MAPPINGS, self
            )
        yield item
