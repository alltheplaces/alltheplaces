import json
import re
from typing import Iterable

from scrapy.http import TextResponse

from locations.hours import OpeningHours
from locations.items import Feature, set_closed
from locations.json_blob_spider import JSONBlobSpider


class GohealthUrgentCareUSSpider(JSONBlobSpider):
    name = "gohealth_urgent_care_us"
    item_attributes = {"brand": "GoHealth Urgent Care", "brand_wikidata": "Q110282081"}
    start_urls = ["https://www.gohealthuc.com/locations"]

    def extract_json(self, response: TextResponse) -> list[dict]:
        return json.loads(response.xpath('//script[@id="__NEXT_DATA__"]/text()').get())["props"]["pageProps"]["centers"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        if self.is_permanently_closed(feature):
            set_closed(item)
        item["branch"] = item.pop("name").strip()
        # "4655 William Flynn Hwy., Suite 110, Allison Park, PA 15101, USA"
        if street := STREET.match(item.get("addr_full") or ""):
            item["street_address"] = street.group(1)
        item["postcode"] = str(item["postcode"])
        item["image"] = feature["image"]["url"].split("?")[0]
        item["website"] = f'https://www.gohealthuc.com/{feature["jv"]}/locations/{feature["uid"]}'
        item["extras"]["ref:google:place_id"] = feature.get("google_place_id")
        item["opening_hours"] = self.parse_opening_hours(feature.get("hoursArr", []))
        yield item

    @staticmethod
    def is_permanently_closed(feature: dict) -> bool:
        """Closed centers stay listed with a "Permanently closed!" alert."""
        return any(
            "permanently closed" in (block.get("text") or "").lower()
            for alert in feature.get("alerts") or []
            for block in alert.get("alert_title") or []
        )

    def parse_opening_hours(self, rules: list[dict]) -> OpeningHours:
        opening_hours = OpeningHours()
        for rule in rules:
            if "Closed" in rule["open_time"].title():
                opening_hours.set_closed(rule["day_of_week"])
                continue
            opening_hours.add_range(
                rule["day_of_week"],
                rule["open_time"],
                rule["close_time"].replace("Midnight", "12:00 am"),
                time_format="%I:%M %p",
            )
        return opening_hours


# The street before ", <city>, <ST> <zip>", with an optional ", USA" or ", United States".
STREET = re.compile(r"^(.+?),\s*[^,]+,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?(?:,\s*(?:USA|United States))?$")
