import json
import re
from typing import Any, Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours
from locations.items import Feature
from locations.playwright_spider import PlaywrightSpider
from locations.settings import DEFAULT_PLAYWRIGHT_SETTINGS


class HobbycoAUSpider(PlaywrightSpider):
    """Spider for Hobbyco hobby stores (Australia).
    Closes #6546
    """

    name = "hobbyco_au"
    item_attributes = {"brand": "Hobbyco", "brand_wikidata": "Q124003864"}
    start_urls = ["https://www.hobbyco.com.au/pages/stores"]
    custom_settings = DEFAULT_PLAYWRIGHT_SETTINGS

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        # The page embeds a JS FeatureCollection using single-quoted syntax.
        # Use brace-counting to extract the full object reliably.
        idx = response.text.find("const stores =")
        if idx < 0:
            self.logger.error("Could not find 'const stores' in page")
            return

        start = response.text.find("{", idx)
        if start < 0:
            return

        depth = 0
        end = start
        for i, c in enumerate(response.text[start:], start):
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

        raw = response.text[start:end]

        # Convert single-quoted JS object to valid JSON
        raw = re.sub(r"'([^']*?)'", lambda mo: '"' + mo.group(1).replace('"', '\\"') + '"', raw)
        raw = re.sub(r",\s*\}", "}", raw)
        raw = re.sub(r",\s*\]", "]", raw)

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse Hobbyco store JSON: %s", e)
            return

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])

            item = Feature()
            item["ref"] = props.get("email", "").split("@")[0] or props.get("address")
            item["branch"] = props.get("address").removeprefix("HOBBYCO ")
            city = props.get("city") or ""
            # The city field also contains the state and postcode, e.g., 'RHODES NSW 2138'.
            if match := re.match(r"^(.*?)\s+([A-Z]{2,3})\s+(\d{4})$", city.strip()):
                item["city"] = match.group(1).title()
                item["state"] = match.group(2)
                item["postcode"] = match.group(3)
            # props.get("postalCode") appears to be a US ZIP code.
            item["phone"] = props.get("phone") or None
            item["email"] = props.get("email") or None
            item["website"] = props.get("maps") or None
            if len(coords) == 2:
                item["lon"], item["lat"] = coords

            if hours_raw := props.get("hours"):
                oh = OpeningHours()
                for line in re.split(r"<br\s*/?>", hours_raw, flags=re.IGNORECASE):
                    oh.add_ranges_from_string(line.strip())
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_TOYS, item)
            yield item
