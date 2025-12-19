from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BankSinopacSpider(JSONBlobSpider):
    name = "bank_sinopac"
    item_attributes = {"brand": "永豐商業銀行", "brand_wikidata": "Q11132721"}
    start_urls = [
        "https://bank.sinopac.com/search/BranchListJson.ashx?callback=callForJsonp5",
        "https://mma.sinopac.com/Share/CustomerService/ATMListJsonNew.ashx?QueryType=1",
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "Branch" in response.url:
            item["addr_full"] = feature["vicinity"]
            apply_category(Categories.BANK, item)
        elif "ATM" in response.url:
            item["street"] = feature["location"]
            apply_category(Categories.ATM, item)
        yield item
