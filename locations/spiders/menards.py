import json
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MenardsSpider(JSONBlobSpider):
    name = "menards"
    item_attributes = {"brand": "Menards", "brand_wikidata": "Q1639897"}
    start_urls = ["https://www.menards.com/store-details/locator.html"]
    requires_proxy = True

    def extract_json(self, response: TextResponse) -> list[dict]:
        return json.loads(response.xpath("//@data-initial-stores").get())

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["number"]
        item["branch"] = item.pop("name")
        item["street_address"] = item.pop("street")
        item["website"] = f"https://www.menards.com/main/storeDetails.html?store={feature['number']}"
        apply_category(Categories.SHOP_DOITYOURSELF, item)

        yield item
