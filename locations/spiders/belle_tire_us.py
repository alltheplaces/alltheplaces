import ast
import json
import re
from typing import Any, Iterable

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class BelleTireUSSpider(Spider):
    name = "belle_tire_us"
    item_attributes = {"brand": "Belle Tire", "brand_wikidata": "Q16984061"}
    start_urls = ["https://www.belletire.com/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        match = re.search(
            r'__staticRouterHydrationData\s*=\s*JSON\.parse\((?P<quote>["\'])(.*?)(?P=quote)\)',
            response.text,
            re.DOTALL,
        )
        if not match:
            return

        for block in (
            json.loads(ast.literal_eval(match.group(0).split("JSON.parse(")[1].rstrip(")")))
            .get("loaderData", {})
            .values()
        ):
            for location in block:
                if not isinstance(location, dict) or "storeNumber" not in location:
                    continue

                item = DictParser.parse(location)
                item["street_address"] = location["streetAddress"]
                item["branch"] = item.pop("name")

                item["opening_hours"] = OpeningHours()
                for rule in location.get("storeSchedule", []):
                    day = rule["dayName"]
                    if rule["storeClosed"] or rule["displayHours"] == "Closed":
                        item["opening_hours"].set_closed(day)
                    else:
                        open_time = rule["openDateTime"].split("T")[1][:5]
                        close_time = rule["closeDateTime"].split("T")[1][:5]
                        item["opening_hours"].add_range(day, open_time, close_time, "%H:%M")

                apply_category(Categories.SHOP_TYRES, item)
                yield item
