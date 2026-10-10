import re
from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours, day_range, sanitise_day


class GoodstartAUSpider(scrapy.Spider):
    name = "goodstart_au"
    item_attributes = {
        "brand": "Goodstart Early Learning",
        "brand_wikidata": "Q24185325",
    }
    allowed_domains = ["goodstart.org.au"]
    start_urls = [
        "https://www.goodstart.org.au/find-centre/api/get-centres/-35.0004451/138.3309724/10000",
    ]
    hours_pattern = re.compile(
        r"(\d{1,2}[:.]\d{2}\s*[ap]m)\s*(?:to|[–-])\s*(\d{1,2}[:.]\d{2}\s*[ap]m)\D*?([A-Za-z]+)\s+to\s+([A-Za-z]+)",
        re.IGNORECASE,
    )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["centres"]:
            if location["name"].endswith("*"):  # not yet open: hours pending service approval
                continue
            item = DictParser.parse(location)
            if item["name"].startswith("Goodstart "):
                item["branch"] = item["name"].removeprefix("Goodstart ")
            item["addr_full"] = location["fullAddress"]
            item["street_address"] = location["address"]
            item["website"] = response.urljoin(item["website"])
            if image_url := location["imageUrl"]:
                item["image"] = response.urljoin(image_url)

            item["opening_hours"] = OpeningHours()
            if match := self.hours_pattern.search(location["hours"] or ""):
                open_time, close_time, start_day, end_day = match.groups()
                start_day, end_day = sanitise_day(start_day, DAYS_EN), sanitise_day(end_day, DAYS_EN)
                if start_day and end_day:
                    for day in day_range(start_day, end_day):
                        item["opening_hours"].add_range(
                            day,
                            open_time.replace(".", ":").replace(" ", ""),
                            close_time.replace(".", ":").replace(" ", ""),
                            time_format="%I:%M%p",
                        )
            else:
                item["opening_hours"].add_ranges_from_string(location["hours"] or "")

            apply_category(Categories.CHILD_CARE, item)
            yield item
