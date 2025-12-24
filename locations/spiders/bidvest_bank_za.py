from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BidvestBankZASpider(JSONBlobSpider):
    name = "bidvest_bank_za"
    item_attributes = {
        "brand": "Bidvest Bank",
        "brand_wikidata": "Q4904284",
    }
    start_urls = ["https://www.bidvestbank.co.za/assets/mock/bidvest-branded-atms.json"]

    def pre_process_data(self, location: dict) -> None:
        location["ref"] = location.pop("Device id")
        location["Latitude"] = location["Latitude"].replace(",", ".")
        location["Longitude"] = location["Longitude"].replace(",", ".")
        location["street_address"] = location.pop("Street Address")

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        apply_category(Categories.ATM, item)
        yield item
