import json
import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class FelleskjopetNOSpider(Spider):
    """Spider for Felleskjøpet agrarian stores (Norway).
    Closes #7036
    """

    name = "felleskjopet_no"
    item_attributes = {"brand": "Felleskjøpet", "brand_wikidata": "Q5442461"}
    start_urls = ["https://www.felleskjopet.no/finn-oss/"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # All location data is embedded as a JSON prop in a ReactDOM.hydrate call
        m = re.search(r'"locations":\[', response.text)
        if not m:
            self.logger.error("Could not find locations data")
            return

        start = m.end()
        depth = 1
        pos = start
        text = response.text
        while pos < len(text) and depth > 0:
            c = text[pos]
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
            pos += 1
        raw = text[start : pos - 1]
        locations = json.loads("[" + raw + "]")

        for loc in locations:
            for unit in loc.get("units", []):
                item = Feature()
                item["ref"] = unit["id"]
                item["branch"] = unit.get("name", "").removeprefix("Butikk ").strip() or None
                item["street_address"] = unit.get("address")
                item["city"] = unit.get("city")
                item["postcode"] = unit.get("zipCode")
                item["phone"] = unit.get("phone") or None
                item["lat"] = loc.get("latitude")
                item["lon"] = loc.get("longitude")
                item["country"] = "NO"

                if hours_raw := unit.get("openingHours"):
                    oh = OpeningHours()
                    oh.add_ranges_from_string(hours_raw)
                    item["opening_hours"] = oh

                apply_category(Categories.SHOP_AGRARIAN, item)
                yield item
