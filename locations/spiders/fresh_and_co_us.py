import json
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature

# The locations page carries every restaurant as a subOrganization of the
# brand's schema.org Organization record, with the address, phone and an
# openingHours list already in OSM syntax.
#
# No coordinates are published: the map links are Google address searches, and
# the newer restaurants publish neither hours nor a phone.
#
# No brand:wikidata is set because the chain has no Wikidata item.


class FreshAndCOUSSpider(Spider):
    name = "fresh_and_co_us"
    item_attributes = {"brand": "fresh&co"}
    allowed_domains = ["www.freshandco.com"]
    start_urls = ["https://www.freshandco.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for block in response.xpath('//script[@type="application/ld+json"]/text()').getall():
            data = json.loads(block)
            if data.get("@type") != "Organization":
                continue

            for location in data.get("subOrganization") or []:
                address = location.get("address") or {}

                item = Feature()
                item["ref"] = (location.get("url") or "").rstrip("/").rsplit("/", 1)[-1]
                # "fresh&co Morristown", "200 W 57th St"
                item["branch"] = (location.get("name") or "").removeprefix("fresh&co").strip()
                item["street_address"] = address.get("streetAddress")
                item["city"] = address.get("addressLocality")
                item["state"] = address.get("addressRegion")
                item["postcode"] = address.get("postalCode")
                item["phone"] = location.get("telephone")
                item["country"] = "US"
                item["website"] = location.get("url")

                item["opening_hours"] = self.parse_opening_hours(location.get("openingHours") or [])

                apply_category(Categories.FAST_FOOD, item)
                item["extras"]["cuisine"] = "salad;sandwich"

                yield item

    @staticmethod
    def parse_opening_hours(opening_hours: list[str]) -> OpeningHours | None:
        """The rules are already in OSM syntax, e.g. "Mo 07:00-20:00"."""
        oh = OpeningHours()

        for rule in opening_hours:
            oh.add_ranges_from_string(rule)

        return oh if oh else None
