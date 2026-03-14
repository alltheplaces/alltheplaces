import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, sanitise_day
from locations.pipelines.address_clean_up import merge_address_lines


class PepSpider(Spider):
    name = "pep"
    start_urls = ["https://www.pepstores.com/cdn/shop/t/6/assets/env.js"]
    brands = {
        "PEP": ("PEP", "Q7166182"),
        "PEP Cell": ("PEP Cell", "Q128802743"),
        "PEP Home": ("PEP Home", "Q128802022"),
    }

    def parse(self, response: Response, **kwargs: Any) -> Any:
        if api_key := re.search(r"middleware_api_key=\"(.+?)\"", response.text):
            token = api_key.group(1)
            yield JsonRequest(
                url="https://pep.commercebridge.tech/rest/v1/store/locator?limit=10000",
                headers={
                    "Authorization": f"Bearer {token}",
                },
                callback=self.parse_locations,
            )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = merge_address_lines([location.get("address1"), location.get("address2")])

            if not location.get("latitude") and not item["street_address"]:  # Not enough address info
                continue

            # Not unique to the POI
            item.pop("image", None)
            item.pop("email", None)

            item["brand"], item["brand_wikidata"] = self.brands.get(location["brand"].strip()) or self.brands["PEP"]
            item["branch"] = item.pop("name").replace(item["brand"], "").strip()

            item["opening_hours"] = OpeningHours()
            if hours_text := location.get("openingHours") or location.get("opening_hours"):
                opening_hours = json.loads(hours_text)
                for rule in opening_hours:
                    if day := sanitise_day(rule):
                        item["opening_hours"].add_range(
                            day, opening_hours[rule]["open"], opening_hours[rule]["close"], "%H:%M:%S"
                        )

            yield item
