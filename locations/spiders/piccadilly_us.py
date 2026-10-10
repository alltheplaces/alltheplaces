import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page is a Next.js app whose restaurant data arrives in the
# React Server Components stream as self.__next_f.push() chunks. Joined and
# decoded, they contain an "initialValue" array with the address as one string,
# coordinates and phone.
#
# Records carry isClosed and isInActive flags, which are honoured.
#
# No opening hours are published on this page.


class PiccadillyUSSpider(Spider):
    name = "piccadilly_us"
    item_attributes = {"brand": "Piccadilly", "brand_wikidata": "Q7190564"}
    allowed_domains = ["www.piccadilly.com"]
    start_urls = ["https://www.piccadilly.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        stream = "".join(
            json.loads(chunk) for chunk in re.findall(r'self\.__next_f\.push\(\[1,(".*?")\]\)', response.text, re.S)
        )
        if (start := stream.find('"initialValue":')) == -1:
            self.logger.error("No locations in the page data")
            return

        locations, _ = json.JSONDecoder().raw_decode(stream[start + len('"initialValue":') :])

        for location in locations:
            if location.get("isClosed") or location.get("isInActive"):
                continue

            # "4996 Stage Rd, Memphis, TN 38128, USA"
            address = re.fullmatch(
                r"(.+?),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?,\s*USA", (location.get("address") or "").strip()
            )
            if not address:
                continue

            item = Feature()
            item["ref"] = location["id"]
            # "MEMPHIS - STAGE ROAD"
            item["branch"] = (location.get("name") or "").title()
            item["street_address"], item["city"], item["state"], item["postcode"] = address.groups()
            item["phone"] = location.get("phoneNumber")
            item["website"] = response.urljoin(location.get("link"))
            if coordinates := location.get("location"):
                item["lat"], item["lon"] = coordinates

            apply_category(Categories.RESTAURANT, item)

            yield item
