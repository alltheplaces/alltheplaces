from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class SaqueEPagueBRSpider(JSONBlobSpider):
    name = "saque_e_pague_br"
    item_attributes = {"brand": "Saque e Pague"}
    start_urls = ["https://saqueepague.blob.core.windows.net/atms/atms.json"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["addr_full"] = feature["address"].replace("-  -", "-")
        item["located_in"] = item.pop("name").split(" -")[0]
        item["name"] = self.item_attributes["brand"]
        apply_category(Categories.ATM, item)
        yield item
