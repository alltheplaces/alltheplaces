import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature

# Each range names its days as a comma separated list: "Mo,Tu,We,Th,Fr 11:00 - 23:00".
# OpeningHours.add_ranges_from_string reads only the last day of such a list and
# drops the rest, so the days are split out here instead.
HOURS = re.compile(
    r"^(?P<days>[A-Za-z]{2}(?:,[A-Za-z]{2})*)\s+(?P<opens>\d{1,2}:\d{2})\s*-\s*(?P<closes>\d{1,2}:\d{2})$"
)


class CycloneAnayasUSSpider(Spider):
    name = "cyclone_anayas_us"
    item_attributes = {"brand": "Cyclone Anaya's"}
    start_urls = ["https://cycloneanaya.com/"]

    @staticmethod
    def hours(specs: list[str]) -> OpeningHours:
        oh = OpeningHours()
        for spec in specs:
            if not (match := HOURS.match(spec.strip())):
                continue
            closes = match["closes"]
            if closes == "00:00":
                # These kitchens close at midnight rather than opening for a minute.
                closes = "24:00"
            for label in match["days"].split(","):
                if day := sanitise_day(label):
                    oh.add_range(day, match["opens"], closes)
        return oh

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            try:
                data = json.loads(block)
            except json.JSONDecodeError:
                continue
            if not isinstance(data, dict) or data.get("@type") != "Organization":
                continue

            for restaurant in data.get("subOrganization") or []:
                address = restaurant.get("address") or {}
                item = Feature()
                item["ref"] = (restaurant.get("@id") or "").rsplit("-", 1)[-1] or None
                # One name is published with a leading space.
                item["branch"] = (restaurant.get("name") or "").strip() or None
                item["website"] = response.url
                item["street_address"] = address.get("streetAddress")
                item["city"] = address.get("addressLocality")
                item["state"] = address.get("addressRegion")
                item["postcode"] = address.get("postalCode")
                item["country"] = address.get("addressCountry")
                item["phone"] = restaurant.get("telephone")

                if geo := restaurant.get("geo"):
                    item["lat"], item["lon"] = geo.get("latitude"), geo.get("longitude")

                item["opening_hours"] = self.hours(restaurant.get("openingHours") or [])

                apply_category(Categories.RESTAURANT, item)
                item["extras"]["cuisine"] = "mexican;tex-mex"
                yield item
