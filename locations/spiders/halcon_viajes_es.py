from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class HalconViajesESSpider(JSONBlobSpider):
    name = "halcon_viajes_es"
    item_attributes = {"brand": "Halcón Viajes", "brand_wikidata": "Q57591939"}
    start_urls = ["https://www.halconviajes.com/agencias/list"]
    locations_key = "agencies"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature["code"]
        item["street_address"] = feature.get("address")
        item["city"] = feature.get("location")
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_TRAVEL_AGENCY, item)
        yield item
