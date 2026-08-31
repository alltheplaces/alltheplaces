from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class DreamlandBbqUSSpider(Spider):
    name = "dreamland_bbq_us"
    item_attributes = {"brand": "Dreamland Bar-B-Que", "brand_wikidata": "Q5306656"}
    start_urls = ["https://dreamlandbbq.com/wp-json/wpgmza/v1/markers?map_id=14"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for marker in response.json():
            if marker.get("map_id") != "14":
                continue
            item = Feature()
            item["ref"] = marker["id"]
            item["name"] = marker["title"].strip()
            item["branch"] = item["name"].removeprefix("Dreamland BBQ").strip()
            item["lat"] = marker["lat"]
            item["lon"] = marker["lng"]
            item["addr_full"] = marker.get("address", "").strip() or None
            item["website"] = marker.get("link") or None

            apply_category(Categories.RESTAURANT, item)

            yield item
