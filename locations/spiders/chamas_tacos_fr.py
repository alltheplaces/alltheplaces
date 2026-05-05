from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ChamasTacosFRSpider(JSONBlobSpider):
    name = "chamas_tacos_fr"
    item_attributes = {"brand": "Chamas Tacos", "brand_wikidata": "Q127411207"}
    allowed_domains = ["chamas-tacos.com"]
    start_urls = ["https://chamas-tacos.com/api/restaurants"]
    locations_key = "restaurants"

    def pre_process_data(self, feature: dict) -> None:
        feature["postcode"] = feature.pop("zip_code", None)

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if feature.get("status") != "published":
            return
        item["ref"] = feature["id"]
        item["branch"] = item.pop("name", None)
        item["website"] = feature.get("order_url")
        yield item
