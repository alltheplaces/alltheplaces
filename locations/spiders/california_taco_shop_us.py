from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.hours import DAYS_EN, OpeningHours
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines

# The site is a single page app whose own /api/locations endpoint returns every
# restaurant with address, coordinates, phone and per day hours.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class CaliforniaTacoShopUSSpider(Spider):
    name = "california_taco_shop_us"
    item_attributes = {"brand": "California Taco Shop"}
    allowed_domains = ["www.californiatacoshopri.com"]
    start_urls = ["https://www.californiatacoshopri.com/api/locations"]

    def start_requests(self) -> Iterable[JsonRequest]:
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json():
            if not location.get("active"):
                continue

            item = Feature()
            item["ref"] = location["id"]
            # "California Taco Shop - Providence"
            item["branch"] = (location.get("name") or "").split(" - ", 1)[-1].strip()
            item["street_address"] = merge_address_lines([location.get("addressLine1"), location.get("addressLine2")])
            item["city"] = location.get("city")
            item["state"] = location.get("state")
            item["postcode"] = location.get("postalCode")
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            item["phone"] = location.get("phone")

            item["opening_hours"] = self.parse_opening_hours(location.get("hours") or [])

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "mexican;tacos"

            yield item

    @staticmethod
    def parse_opening_hours(hours: list[dict]) -> OpeningHours | None:
        """Each entry is {"day": "monday", "open": "09:00", "close": "23:00"}."""
        oh = OpeningHours()

        for rule in hours:
            if not (day := DAYS_EN.get((rule.get("day") or "").title())):
                continue
            if rule.get("closed"):
                oh.set_closed(day)
                continue
            if (opens := rule.get("open")) and (closes := rule.get("close")):
                oh.add_range(day, opens, "24:00" if closes == "00:00" else closes)

        return oh if oh else None
