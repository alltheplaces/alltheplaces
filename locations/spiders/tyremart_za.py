from typing import Iterable

from scrapy.http import JsonRequest, TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TyremartZASpider(JSONBlobSpider):
    name = "tyremart_za"
    item_attributes = {"brand": "Tyremart", "brand_wikidata": "Q123382009"}
    start_urls = ["https://www.tyremart.co.za/api/branches?brandId=1&limit=100&page=1"]
    locations_key = "data"

    def parse(self, response: TextResponse) -> Iterable[Feature | JsonRequest]:
        yield from super().parse(response)
        if (data := response.json())["hasMore"]:
            yield JsonRequest(
                url="https://www.tyremart.co.za/api/branches?brandId=1&limit=100&page={}".format(data["page"] + 1)
            )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("Tyremart ")
        item["street_address"] = item.pop("addr_full")
        item["email"] = feature["branchLocatorEmail"]
        apply_category(Categories.SHOP_TYRES, item)
        yield item
