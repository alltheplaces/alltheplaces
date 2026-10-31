import re
from typing import Iterable

from parsel import Selector

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours, day_range, sanitise_day
from locations.items import Feature
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class ChopStopUSSpider(SuperStoreFinderSpider):
    name = "chop_stop_us"
    item_attributes = {"brand": "Chop Stop"}
    allowed_domains = ["chopstop.com"]

    def parse_item(self, item: Feature, location: Selector) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)

        # The store finder collapses whitespace in addr_full, so the raw XML
        # value is read again here for the double space that separates the
        # street from the city.
        raw_address = location.xpath("./address/text()").get() or ""
        if address := re.match(r"^(.*?)\s{2,}(.+?),\s+([A-Z]{2})\s+(\d{5})", raw_address, re.DOTALL):
            item.pop("addr_full", None)
            street, city, state, postcode = address.groups()
            item["street_address"] = re.sub(r"\s+", " ", street).strip()
            item["city"] = re.sub(r"\s+", " ", city).strip()
            item["state"] = state
            item["postcode"] = postcode

        item["opening_hours"] = self.parse_opening_hours(location)

        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "salad"

        yield item

    @staticmethod
    def parse_opening_hours(location: Selector) -> OpeningHours | None:
        oh = OpeningHours()

        for rule in (location.xpath("./custom_field1/text()").get() or "").split("<br/>"):
            if not (
                times := re.search(
                    r"(\d{1,2}:\d{2}\s*[ap]m)\s*-\s*(\d{1,2}:\d{2}\s*[ap]m)",
                    rule,
                    re.I,
                )
            ):
                continue

            days = rule[: times.start()].strip(" -")
            if not days or re.search(r"daily", rule, re.I):
                day_names = list(DAYS_EN.values())
            elif re.search(r"weekends?", days, re.I):
                day_names = ["Sa", "Su"]
            else:
                day_names = []
                for token in re.split(r"[/&]|\band\b", days):
                    if "-" in token:
                        start, end = [sanitise_day(part) for part in token.split("-", 1)]
                        if start and end:
                            day_names.extend(day_range(start, end))
                    elif day := sanitise_day(token):
                        day_names.append(day)

            if day_names:
                oh.add_days_range(
                    day_names,
                    times.group(1).replace(" ", "").lower(),
                    times.group(2).replace(" ", "").lower(),
                    time_format="%I:%M%p",
                )

        return oh if oh.as_opening_hours() else None
