import re
from typing import Any, Iterable

from chompjs import chompjs
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
        data = chompjs.parse_js_object(re.search(r"const stores = (.+?);", response.text, re.DOTALL).group(1))

        for feature in data.get("features", []):
            props = feature.get("properties", {})
            item = Feature()
            item["geometry"] = feature["geometry"]
            item["ref"] = props.get("email", "").split("@")[0] or props.get("address")
            item["name"] = self.item_attributes["brand"]
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

            if hours_raw := props.get("hours"):
                oh = OpeningHours()
                for line in re.split(r"<br\s*/?>", hours_raw, flags=re.IGNORECASE):
                    oh.add_ranges_from_string(line.strip())
                item["opening_hours"] = oh

            apply_category(Categories.SHOP_TOYS, item)
            yield item
