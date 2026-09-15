import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# Carolina Ale House runs on Popmenu, which embeds its whole Apollo GraphQL
# cache in the locations page as window.POPMENU_APOLLO_STATE. Restaurants are
# the RestaurantLocation entries in that cache.
#
# The cache also holds stub entries carrying nothing but an id, and one
# disabled placeholder record, both of which are skipped.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class CarolinaAleHouseUSSpider(Spider):
    name = "carolina_ale_house_us"
    item_attributes = {"brand": "Carolina Ale House"}
    allowed_domains = ["www.carolinaalehouse.com"]
    start_urls = ["https://www.carolinaalehouse.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for key, location in self.parse_apollo_state(response).items():
            if not key.startswith("RestaurantLocation:"):
                continue
            if not location.get("isLocationEnabled") or location.get("isLocationClosed"):
                continue

            item = Feature()
            item["ref"] = location["slug"]
            item["branch"] = location["name"]
            item["street_address"] = location.get("streetAddress")
            item["city"] = location.get("city")
            item["state"] = location.get("state")
            item["postcode"] = location.get("postalCode")
            item["country"] = location.get("country")
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lng")
            item["phone"] = location.get("displayPhone")
            item["email"] = location.get("email")
            item["website"] = response.urljoin(f"/locations/{location['slug']}")

            item["opening_hours"] = self.parse_opening_hours(location)

            apply_category(Categories.RESTAURANT, item)
            item["extras"]["cuisine"] = "american"

            yield item

    @staticmethod
    def parse_apollo_state(response: Response) -> dict:
        """Extracts the JSON object assigned to window.POPMENU_APOLLO_STATE."""
        start = re.search(r"window\.POPMENU_APOLLO_STATE\s*=\s*", response.text).end()
        depth = 0
        for offset, character in enumerate(response.text[start:]):
            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(response.text[start : start + offset + 1])
        return {}

    @staticmethod
    def parse_opening_hours(location: dict) -> OpeningHours | None:
        """schemaHours is already a list of rules such as "Su 11:00-02:00"."""
        oh = OpeningHours()
        for rule in location.get("schemaHours") or []:
            if match := re.fullmatch(r"([A-Za-z]{2})\s+(\d{2}:\d{2})-(\d{2}:\d{2})", rule.strip()):
                oh.add_range(*match.groups())
        return oh if oh.as_opening_hours() else None
