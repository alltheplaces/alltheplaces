from typing import Iterable

from scrapy import Request

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

    def start_requests(self) -> Iterable[Request]:
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
            if meta_data.get("salesUnitFlag") == "Ya":
                apply_category(Categories.SHOP_CAR, item)
                apply_yes_no(Extras.CAR_REPAIR, item, meta_data.get("serviceFlag") == "Ya")
                apply_yes_no(Extras.CAR_PARTS, item, meta_data.get("sparepartFlag") == "Ya")
            elif meta_data.get("serviceFlag") == "Ya":
                apply_category(Categories.SHOP_CAR_REPAIR, item)
                apply_yes_no(Extras.CAR_PARTS, item, meta_data.get("sparepartFlag") == "Ya")
            elif meta_data.get("sparepartFlag") == "Ya":
                apply_category(Categories.SHOP_CAR_PARTS, item)
            else:
                self.logger.error(f"No type present for: {item['ref']}, {item['name']}")
            # TODO: hours
            yield item
