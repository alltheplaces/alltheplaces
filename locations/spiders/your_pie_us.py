import html
import re
from typing import Any, Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature

# The locations page holds every restaurant in a window.blockLocations
# JavaScript array with the address as one string, coordinates, phone and the
# restaurant's page.
#
# The Thanx ordering link carries the chain's own location id, which is used as
# the ref where present.
#
# No opening hours are published on this page.


class YourPieUSSpider(Spider):
    name = "your_pie_us"
    item_attributes = {"brand": "Your Pie", "brand_wikidata": "Q17060193"}
    allowed_domains = ["yourpie.com"]
    start_urls = ["https://yourpie.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if not (locations := re.search(r"window\.blockLocations\s*=\s*", response.text)):
            self.logger.error("No locations on the locations page")
            return

        for location in chompjs.parse_js_object(response.text[locations.end() :]):
            # "100 W. Foothill Blvd, Azusa, CA 91702, US"
            address = re.fullmatch(
                r"(.+),\s*([^,]+),\s*([A-Z]{2})\s+(\d{5})(?:-\d{4})?,\s*([A-Z]{2})",
                (location.get("address") or "").strip(),
            )
            if not address:
                continue

            item = Feature()
            item["street_address"], item["city"], item["state"], item["postcode"], item["country"] = address.groups()
            item["lat"] = location.get("lat")
            item["lon"] = location.get("lng")
            item["phone"] = location.get("phone")
            item["website"] = location.get("link")
            # "Azusa, CA - NOW OPEN!"
            item["branch"] = (
                re.split(r"\s+[\u2013-]\s+", html.unescape(location.get("title") or ""))[0].rsplit(",", 1)[0].strip()
            )

            order_url = location.get("order_url") or ""
            if store_id := re.search(r"location=(\d+)", order_url):
                item["ref"] = store_id.group(1)
            else:
                item["ref"] = (item["website"] or "").rstrip("/").rsplit("/", 1)[-1]

            apply_category(Categories.FAST_FOOD, item)
            item["extras"]["cuisine"] = "pizza"

            yield item
