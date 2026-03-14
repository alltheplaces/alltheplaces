from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class MovistarESSpider(JSONBlobSpider):
    name = "movistar_es"
    item_attributes = {"brand": "Movistar", "brand_wikidata": "Q967735"}
    start_urls = ["https://tiendas.movistar.es/pages_api/v1/locations"]
    locations_key = "locations"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name").replace("Tienda Movistar ", "")
        oh = OpeningHours()
        for day, times in feature["hours"].items():
            for time in times:
                oh.add_range(day, time["from"], time["to"])
        item["opening_hours"] = oh
        item["website"] = feature["pages"]["store-page"]
        apply_category(Categories.SHOP_MOBILE_PHONE, item)
        yield item
