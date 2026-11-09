import re
from typing import Iterable

from locations.categories import Categories, apply_category
from locations.hours import DAYS_3_LETTERS, OpeningHours
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class NormsUSSpider(StoreRocketSpider):
    name = "norms_us"
    item_attributes = {"brand": "NORMS", "brand_wikidata": "Q7053150"}
    storerocket_id = "MZponDn8DN"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["ref"] = str(location["id"])
        item["branch"] = item.pop("name", None)
        item.pop("addr_full", None)

        # "1125 N Euclid St, Anaheim, CA 92801"
        if address := re.fullmatch(
            r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})", (location.get("display_address") or "").strip()
        ):
            item["street_address"], item["city"], item["state"], item["postcode"] = address.groups()

        # The phone field holds order buttons; the number is in their tel: link.
        markup = " ".join(str(field.get("pivot_field_value") or "") for field in location.get("fields") or []) + str(
            location.get("phone") or ""
        )
        if phone := re.search(r"tel:\+?1?(\d{10})", markup):
            item["phone"] = phone.group(1)

        item["opening_hours"] = self.parse_opening_hours(location)

        apply_category(Categories.RESTAURANT, item)
        item["extras"]["cuisine"] = "american"

        yield item

    @staticmethod
    def parse_opening_hours(location: dict) -> OpeningHours | None:
        """Days hold "Open 24 Hours", "7AM-10PM", "7AM - 11PM" or "7AM,11PM"."""
        oh = OpeningHours()

        for day, field in zip(DAYS_3_LETTERS, ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]):
            hours = (location.get(field) or "").strip()
            if re.fullmatch(r"(?i)open 24 hours", hours):
                oh.add_range(day, "00:00", "24:00")
                continue
            if times := re.fullmatch(
                r"(\d{1,2}(?::\d{2})?\s*[ap]m)\s*[-,]\s*(\d{1,2}(?::\d{2})?\s*[ap]m)", hours, re.I
            ):
                oh.add_range(
                    day,
                    times.group(1),
                    times.group(2),
                    time_format=["%I:%M%p", "%I:%M %p", "%I%p", "%I %p"],
                )

        return oh if oh else None
