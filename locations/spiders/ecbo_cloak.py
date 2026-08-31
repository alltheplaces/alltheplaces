from typing import AsyncIterator, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.geo import city_locations
from locations.items import Feature


class EcboCloakSpider(Spider):
    name = "ecbo_cloak"
    item_attributes = {"brand": "ecbo cloak"}
    skip_auto_cc_domain = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen: set[str] = set()

    async def start(self) -> AsyncIterator[JsonRequest]:
        for city in city_locations("JP", 15000):
            yield JsonRequest(
                url=f"https://search.ecbo.io/api/v1/search?latitude={city['latitude']}&longitude={city['longitude']}",
            )
        for city in city_locations("TW", 15000):
            yield JsonRequest(
                url=f"https://search.ecbo.io/api/v1/search?latitude={city['latitude']}&longitude={city['longitude']}",
            )

    def parse(self, response: Response, **kwargs) -> Iterable[Feature]:
        for location in response.json().get("locationUnits", []):
            ref = location.get("encrypted_id")
            if not ref or ref in self._seen:
                continue
            self._seen.add(ref)

            loc = location.get("location", {})
            item = Feature()
            item["ref"] = ref
            item["name"] = location.get("name") or location.get("en_name")
            item["extras"]["name:en"] = location.get("en_name")
            item["lat"] = loc.get("latitude")
            item["lon"] = loc.get("longitude")
            item["website"] = f"https://cloak.ecbo.io/ja/space/{ref}"
            item["extras"]["website:en"] = f"https://cloak.ecbo.io/en/space/{ref}"
            item["extras"]["website:ja"] = f"https://cloak.ecbo.io/ja/space/{ref}"
            item["extras"]["website:zh-TW"] = f"https://cloak.ecbo.io/zh-TW/space/{ref}"
            item["image"] = location.get("main_image_url")

            basic = location.get("basic_info", {})

            if basic.get("available_24_hour"):
                item["opening_hours"] = "24/7"
            apply_yes_no("elevator", item, basic.get("has_elevator"))
            apply_yes_no("socket:nema_1_15", item, basic.get("has_charge"))
            apply_yes_no("language:en", item, basic.get("available_in_english"))
            apply_yes_no(Extras.WIFI, item, basic.get("has_wifi"))

            location_type = location.get("type")
            if location_type == "space":
                apply_category(Categories.LEFT_LUGGAGE, item)
            else:
                # pudo and locker_cluster types are luggage lockers
                apply_category(Categories.LUGGAGE_LOCKER, item)

            yield item
