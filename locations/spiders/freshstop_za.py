import re
from typing import Iterable

from scrapy.http import TextResponse
from scrapy.http.request.form import FormRequest

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class FreshstopZASpider(JSONBlobSpider):
    name = "freshstop_za"
    item_attributes = {"brand": "FreshStop", "brand_wikidata": "Q116620734"}
    locations_key = "data"

    async def start(self):
        yield FormRequest(
            url="https://freshstop.co.za/wp-admin/admin-ajax.php",
            formdata={
                "action": "list_stores",
                "lat": "28.6327",
                "lng": "77.2198",
            },
        )

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        item["website"] = feature["store_permalink"]
        item["lat"], item["lon"] = re.search(r".*=(-?\d+\.\d+),(-?\d+\.\d+)", feature["maps_url"]).groups()

        apply_category(Categories.SHOP_CONVENIENCE, item)

        yield item
