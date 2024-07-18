import re
from typing import Any
from urllib.parse import urljoin

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.hours import DAYS_FULL, OpeningHours
from locations.items import Feature


class HaysTravelGBSpider(Spider):
    name = "hays_travel_gb"
    item_attributes = {"brand": "Hays Travel", "brand_wikidata": "Q70250954"}
    start_urls = ["https://branches.haystravel.co.uk/api/branches"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        items = response.json()["data"]

        for location in items:
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            item["branch"] = location["name"]
            item["street_address"] = location["address"]
            item["city"] = location["name"]
            item["postcode"] = location["postcode"]
            # This is not true for all cases - example Hull Northpoint
            item["website"] = urljoin("https://www.haystravel.co.uk/branches/", "-".join(location["name"].split()))
            item["phone"] = location["phone"]
            item["email"] = location["email"]

            oh = OpeningHours()
            for day in map(str.lower, DAYS_FULL):
                if rule := location.get(f"{day}_hours"):
                    for start_hour, start_minute, start_zone, end_hour, end_minute, end_zone in re.findall(
                        r"(\d*)[:.](\d\d)\s*(am|pm)?\s*-\s*(\d*)[:.](\d\d)\s*(am|pm)?", rule
                    ):
                        if start_zone:
                            start_hour = int(start_hour)
                            if start_zone == "pm" and start_hour < 12:
                                start_hour += 12
                            start = f"{start_hour:02d}:{start_minute}"
                            end_hour = int(end_hour)
                            if end_zone == "pm" and end_hour < 12:
                                end_hour += 12
                            end = f"{end_hour:02d}:{end_minute}"
                        else:
                            start = f"{start_hour}:{start_minute}"
                            end = f"{end_hour}:{end_minute}"
                        oh.add_range(day, start, end)
            item["opening_hours"] = oh.as_opening_hours()

            yield item
