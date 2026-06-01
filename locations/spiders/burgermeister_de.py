from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class BurgermeisterDESpider(JSONBlobSpider):
    name = "burgermeister_de"
    item_attributes = {"brand": "Burgermeister", "brand_wikidata": "Q116382535"}
    start_urls = [
        "https://burgermeister.com/wp-admin/admin-ajax.php?filter=%7B%22map_id%22%3A%226%22%2C%22mashupIDs%22%3A%5B%5D%2C%22customFields%22%3A%5B%5D%7D&route=%2Ffeatures%2F&action=wpgmza_rest_api_request"
    ]
    locations_key = "markers"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "COMING SOON" in feature.get("description", ""):
            return

        item["branch"] = item.pop("name", "").split(" | ")[-1].strip()
        item["image"] = feature.get("pic")

        apply_category(Categories.FAST_FOOD, item)

        yield item
