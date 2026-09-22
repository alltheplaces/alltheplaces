import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature

# The location directory is a Next.js page whose shop data arrives in the React
# Server Components stream as self.__next_f.push() chunks. Joined and decoded,
# the stream holds one record per shop with address, coordinates, phone and
# per day hours. Records can appear more than once, so they are keyed on id.
#
# The /locations page carries only CMS entries with an address slug, which is
# why the directory page is used instead.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class PopupBagelsUSSpider(Spider):
    name = "popup_bagels_us"
    item_attributes = {"brand": "PopUp Bagels"}
    allowed_domains = ["www.popupbagels.com"]
    start_urls = ["https://www.popupbagels.com/location-directory"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        stream = "".join(
            json.loads(chunk) for chunk in re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', response.text, re.S)
        )

        locations = {}
        decoder = json.JSONDecoder()
        for match in re.finditer(r'\{"id":"[^"]+","name":"[^"]*","slug":"[^"]*","extref"', stream):
            location, _ = decoder.raw_decode(stream[match.start() :])
            locations[location["id"]] = location

        if not locations:
            self.logger.error("No shops in the directory page data")

        for location in locations.values():
            address = location.get("address") or {}

            item = Feature()
            item["ref"] = location["id"]
            item["branch"] = location.get("name")
            item["street_address"] = address.get("street")
            item["city"] = address.get("city")
            item["state"] = address.get("state")
            item["postcode"] = address.get("zip")
            item["country"] = address.get("country")
            item["lat"] = address.get("latitude")
            item["lon"] = address.get("longitude")
            item["phone"] = location.get("telephone")

            item["opening_hours"] = self.parse_opening_hours((location.get("hours") or {}).get("business") or {})

            apply_category(Categories.SHOP_BAKERY, item)
            item["extras"]["cuisine"] = "bagel"

            yield item

    @staticmethod
    def parse_opening_hours(business: dict) -> OpeningHours | None:
        """Each day is {"start": "2026-09-21 07:00:00", "end": "2026-09-21 15:00:00", "is_open": true}."""
        oh = OpeningHours()

        for day, rule in business.items():
            if day not in DAYS_3_LETTERS or not rule.get("is_open"):
                continue
            if (opens := (rule.get("start") or "")[11:16]) and (closes := (rule.get("end") or "")[11:16]):
                oh.add_range(day, opens, closes)

        return oh if oh else None
