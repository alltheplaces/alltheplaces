import re
from typing import Any, Iterable

import chompjs
from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.items import Feature

# Mamoun's uses a BentoBox store locator, which passes every restaurant to a
# storeLocatorConfig() call on the locator page as a JavaScript object literal.
#
# Unlike the other BentoBox sites, this one leaves structured_hours empty and
# writes the hours as HTML instead, with "*Take-Out" and "*Delivery" notes
# alongside the restaurant's own hours.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class MamounsFalafelUSSpider(Spider):
    name = "mamouns_falafel_us"
    item_attributes = {"brand": "Mamoun's Falafel"}
    allowed_domains = ["www.mamouns.com"]
    start_urls = ["https://www.mamouns.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        config = chompjs.parse_js_object(response.text.split("storeLocatorConfig(", 1)[1])

        for location in config["locations"]:
            item = DictParser.parse(location)
            item["ref"] = location["id"]
            # "New Haven, CT"
            item["branch"] = re.sub(r",\s*[A-Za-z]{2,3}$", "", location.get("name") or "").strip()
            item["name"] = None
            item.pop("addr_full", None)
            item["street"] = None
            item["street_address"] = location.get("street")
            item["phone"] = location.get("phone_number")
            item["website"] = response.urljoin(location["url"])

            item["opening_hours"] = self.parse_opening_hours(location.get("hours") or "")

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "falafel;middle_eastern"

            yield item

    @staticmethod
    def parse_opening_hours(hours: str) -> OpeningHours | None:
        """The hours are HTML lines such as "Sunday - Thursday: 11 am - 12 am"."""
        oh = OpeningHours()

        for line in Selector(text=hours).xpath("//text()").getall():
            line = re.sub(r"\s+", " ", line.replace("\xa0", " ")).replace("\u2013", "-").strip()
            # "*Take-Out" and "*Delivery" are service notes, not opening hours.
            if line.startswith("*"):
                continue
            if not (
                rule := re.fullmatch(
                    r"([A-Za-z]{3,9})\s*(?:-\s*([A-Za-z]{3,9}))?\s*:\s*"
                    r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*-\s*(\d{1,2}(?::\d{2})?\s*[ap]m)",
                    line,
                    re.I,
                )
            ):
                continue

            start, end = sanitise_day(rule.group(1)), sanitise_day(rule.group(2) or rule.group(1))
            if not start or not end:
                continue

            oh.add_days_range(
                day_range(start, end),
                MamounsFalafelUSSpider.normalise_time(rule.group(3)),
                MamounsFalafelUSSpider.normalise_time(rule.group(4)),
                time_format="%I:%M%p",
            )

        return oh if oh else None

    @staticmethod
    def normalise_time(value: str) -> str:
        value = value.replace(" ", "").upper()
        return value if ":" in value else re.sub(r"(\d+)", r"\1:00", value, count=1)
