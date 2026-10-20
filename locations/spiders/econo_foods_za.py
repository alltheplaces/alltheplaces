from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class EconoFoodsZASpider(JSONBlobSpider):
    name = "econo_foods_za"
    item_attributes = {"brand": "Econo Foods", "brand_wikidata": "Q130406968"}
    start_urls = [
        "https://profilepilot.actonia.co.za/api/widget/locations?orgId=ae9af81f-342a-4046-9c6e-38b97124df13&limit=500"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}  # robots.txt blanket-disallows /api/
    locations_key = "data"

    def pre_process_data(self, feature: dict) -> None:
        coordinates = feature.get("latlng") or {}
        feature["latitude"], feature["longitude"] = coordinates.get("latitude"), coordinates.get("longitude")

    def post_process_item(self, item: Feature, response: Response, feature: dict, **kwargs: Any) -> Iterable[Feature]:
        item["ref"] = feature["storeCode"]
        item["branch"] = item.pop("name").removeprefix("Econo Foods ").removeprefix("Econofoods ")
        item["website"] = None

        address = feature.get("address") or {}
        item["street_address"] = ", ".join(address.get("addressLines") or []) or None
        item["country"] = address.get("regionCode")

        item["opening_hours"] = OpeningHours()
        for day, times in (feature.get("hours") or {}).items():
            if times == "Closed":
                item["opening_hours"].set_closed(DAYS_EN[day])
            elif times and "-" in times:
                start, end = times.split("-", 1)
                item["opening_hours"].add_range(DAYS_EN[day], start.strip(), end.strip())

        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
