import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature

# The locations page is a Next.js app built with Builder.io. Its restaurant
# data arrives in the React Server Components stream as self.__next_f.push()
# chunks; joined and decoded, they contain a "locations" array with address,
# coordinates, per day hours and service flags for every restaurant.


class ZippysUSSpider(Spider):
    name = "zippys_us"
    item_attributes = {"brand": "Zippy's", "brand_wikidata": "Q8072671"}
    allowed_domains = ["www.zippys.com"]
    start_urls = ["https://www.zippys.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        stream = "".join(
            json.loads(chunk) for chunk in re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', response.text, re.S)
        )
        if (start := stream.find('"locations":[{"id"')) == -1:
            self.logger.error("No locations in the page data")
            return

        locations, _ = json.JSONDecoder().raw_decode(stream[start + len('"locations":') :])

        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = location["id"]
            item["branch"] = location.get("name")
            item["name"] = None
            item["website"] = f"https://www.zippys.com/locations/{location['slug']}/"
            item["image"] = None

            item["opening_hours"] = self.parse_opening_hours((location.get("hours") or {}).get("business") or {})

            supports = location.get("supports") or {}
            apply_yes_no(Extras.DRIVE_THROUGH, item, supports.get("drivethru"), False)
            apply_yes_no(Extras.TAKEAWAY, item, supports.get("pickUp"), False)
            apply_yes_no(Extras.INDOOR_SEATING, item, supports.get("dineIn"), False)

            apply_category(Categories.FAST_FOOD, item)

            yield item

    @staticmethod
    def parse_opening_hours(business: dict) -> OpeningHours | None:
        """Each day is {"open": "6 AM", "close": "12 AM", "allDay": false}."""
        oh = OpeningHours()

        for day_name, rule in business.items():
            if not (day := DAYS_EN.get(day_name)):
                continue
            if rule.get("allDay"):
                oh.add_range(day, "00:00", "24:00")
                continue
            if not rule.get("open") or not rule.get("close"):
                continue

            oh.add_range(
                day,
                ZippysUSSpider.normalise_time(rule["open"]),
                ZippysUSSpider.normalise_time(rule["close"]),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        """ "6 AM" -> "6:00AM"."""
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
