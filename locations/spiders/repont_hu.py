from typing import Iterable

from scrapy.http import JsonRequest, Request

from locations.categories import Categories, apply_category
from locations.json_blob_spider import JSONBlobSpider


class RepontHUSpider(JSONBlobSpider):
    name = "repont_hu"
    item_attributes = {
        "brand": "REpont",
        "brand_wikidata": "Q130348902",
        "operator": "MOHU MOL Hulladékgazdálkodási Zrt.",
        "operator_wikidata": "Q130207606",
    }

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            "https://map.mohu.hu/api/Map/SearchWastePoints",
            data={"wastePointTypes": ["repont"], "hideDrsPoints": False},
        )

    def post_process_item(self, item, response, location):
        item["name"] = None
        item["street_address"] = item.pop("addr_full")
        apply_category(Categories.VENDING_MACHINE_BOTTLE_RETURN, item)
        yield item
