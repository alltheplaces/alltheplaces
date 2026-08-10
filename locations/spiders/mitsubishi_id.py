from copy import deepcopy
from typing import AsyncIterator

from scrapy.http import Request

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import city_locations, country_iseadgg_centroids
from locations.json_blob_spider import JSONBlobSpider


class MitsubishiIDSpider(JSONBlobSpider):
    name = "mitsubishi_id"
    item_attributes = {
        "brand": "Mitsubishi",
        "brand_wikidata": "Q36033",
    }
    locations_key = "data"

    async def start(self) -> AsyncIterator[Request]:
        # 40 is the maximum and 12 is the default number of results per page.
        # Seems there is no way to go over 40 results for all pages.
        for lat, lon in country_iseadgg_centroids(["ID"], 24):
            yield Request(
                f"https://api-web.mitsubishi-motors.co.id/api/v1/dealers?latitude={lat}&longitude={lon}&per_page=40"
            )
        # Do one more round of requests to get more results
        for city in city_locations("ID"):
            yield Request(
                f"https://api-web.mitsubishi-motors.co.id/api/v1/dealers?latitude={city['latitude']}&longitude={city['longitude']}&per_page=40"
            )

    def post_process_item(self, item, response, location):
        if location.get("status") == "Aktif":
            item["street_address"] = item.pop("addr_full")

            meta_data = location.get("meta_data", {})
            has_sales = meta_data.get("salesUnitFlag") == "Ya"
            has_service = meta_data.get("serviceFlag") == "Ya"
            has_parts = meta_data.get("sparepartFlag") == "Ya"

            if not has_sales and not has_service and not has_parts:
                self.logger.error(f"No type present for: {item['ref']}, {item['name']}")
                return
            if has_sales:
                shop_item = deepcopy(item)
                shop_item["ref"] = f"{item['ref']}-shop"
                apply_category(Categories.SHOP_CAR, shop_item)
                apply_yes_no(Extras.CAR_REPAIR, shop_item, has_service)
                apply_yes_no(Extras.CAR_PARTS, shop_item, has_parts)
                yield shop_item

            if has_service:
                repair_item = deepcopy(item)
                repair_item["ref"] = f"{item['ref']}-repair"
                apply_category(Categories.SHOP_CAR_REPAIR, repair_item)
                apply_yes_no(Extras.CAR_PARTS, repair_item, has_parts)
                yield repair_item

            if has_parts:
                parts_item = deepcopy(item)
                parts_item["ref"] = f"{item['ref']}-parts"
                apply_category(Categories.SHOP_CAR_PARTS, parts_item)
                yield parts_item
