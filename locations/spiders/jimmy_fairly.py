import json
import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.hours import OpeningHours, sanitise_day
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class JimmyFairlySpider(JSONBlobSpider):
    name = "jimmy_fairly"
    item_attributes = {"brand": "Jimmy Fairly", "brand_wikidata": "Q104825419"}
    start_urls = ["https://www.jimmyfairly.com/pages/stores"]

    def extract_json(self, response):
        data = response.xpath('//script[contains(@x-ref,"json")]/text()').get()

        if not data:
            raise ValueError("data not found")

        data = json.loads(data)
        return [f["properties"] for f in data["features"]]

    def parse_opening_hours(self, rules: dict) -> OpeningHours:
        oh = OpeningHours()
        for day, time in rules.items():
            day = sanitise_day(day)
            if not day:
                continue

            if time == "" or time.lower() == "closed":
                oh.set_closed(day)
            else:
                for start, end in re.findall(r"(\d\d\d\d)-(\d\d\d\d)", time.replace("|", "-")):
                    oh.add_range(day, start, end, time_format="%H%M")
        return oh

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", "").removeprefix("Jimmy Fairly - ")
        if location.get("url") is not None:
            item["website"] = "https://www.jimmyfairly.com" + location["url"]

        if location.get("opening_hours") is not None:
            try:
                item["opening_hours"] = self.parse_opening_hours(location["opening_hours"])
            except Exception:
                pass

        apply_category(Categories.SHOP_OPTICIAN, item)

        yield item
