import json
import re
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class ExkiSpider(JSONBlobSpider):
    name = "exki"
    item_attributes = {"brand": "Exki", "brand_wikidata": "Q251760"}
    start_urls = ["https://www.exki.com/restaurants"]

    def extract_json(self, response: Response) -> list[dict]:
        match = re.search(r"var locations = (\[.*?]);", response.text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        return []

    def parse_opening_hours(self, item: Feature) -> OpeningHours:
        oh = OpeningHours()
        try:
            for day in DAYS_FULL:
                day_lower = day.lower()
                open_time = item.get(f"{day_lower}_open")
                close_time = item.get(f"{day_lower}_close")

                if open_time and close_time:
                    # close_time format is "- HH:MM", remove the dash
                    close_time = close_time.strip().lstrip("-").strip()
                    oh.add_range(day, open_time, close_time)
        except:
            self.crawler.stats.inc_value("failed_parsing_hours")

        return oh

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        feature["street_address"] = feature.pop("address")

        item = DictParser.parse(feature)
        item["branch"] = feature.get("name")
        item["opening_hours"] = self.parse_opening_hours(item)

        apply_category(Categories.FAST_FOOD, item)
        yield item
