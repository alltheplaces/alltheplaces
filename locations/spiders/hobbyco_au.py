import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature


class HobbycoAUSpider(Spider):
    """Spider for Hobbyco hobby stores (Australia).
    Closes #6546
    """

    name = "hobbyco_au"
    item_attributes = {"brand": "Hobbyco", "brand_wikidata": "Q124003864"}
    start_urls = ["https://www.hobbyco.com.au/pages/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The page embeds a JS FeatureCollection using single-quoted syntax.
        # Extract the features array and convert to JSON-parseable form.
        m = re.search(r"const stores\s*=\s*\{.*?'features'\s*:\s*(\[.*?\])\s*\}", response.text, re.DOTALL)
        if not m:
            return

        # Convert single-quoted JS object to valid JSON
        raw = m.group(1)
        raw = re.sub(r"'([^']*)'", lambda mo: '"' + mo.group(1).replace('"', '\\"') + '"', raw)
        raw = re.sub(r",\s*\}", "}", raw)
        raw = re.sub(r",\s*\]", "]", raw)

        import json

        try:
            features = json.loads(raw)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse Hobbyco store JSON")
            return

        for feature in features:
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])

            item = Feature()
            item["ref"] = props.get("email", "").split("@")[0] or props.get("address")
            item["branch"] = props.get("address")
            item["city"] = props.get("city")
            item["postcode"] = props.get("postalCode")
            item["country"] = "AU"
            item["phone"] = props.get("phone") or None
            item["email"] = props.get("email") or None
            item["website"] = props.get("maps") or None
            if len(coords) == 2:
                item["lon"], item["lat"] = coords

            if hours_raw := props.get("hours"):
                oh = OpeningHours()
                # Format: "Monday 10am - 6pm<br>Tuesday 10am - 6pm<br>..."
                for line in re.split(r"<br\s*/?>", hours_raw, flags=re.IGNORECASE):
                    oh.add_ranges_from_string(line.strip())
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_TOYS, item)
            yield item
