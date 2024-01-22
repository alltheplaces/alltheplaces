import json
import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class SizzlerUSSpider(Spider):
    name = "sizzler_us"
    item_attributes = {"brand": "Sizzler", "brand_wikidata": "Q1848822"}
    start_urls = ["https://sizzler.com/locations/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in json.loads(re.search(r"var locations_meta = (\[.+\]);", response.text).group(1)):
            item = Feature()
            item["ref"] = location["location"]["branch_id"]
            item["website"] = location["single_page"]
            item["phone"] = location["location"]["store_phone_number"]
            item["branch"] = location["location"]["branch_name"]
            item["lat"] = location["location"]["map_pin"]["lat"]
            item["lon"] = location["location"]["map_pin"]["lng"]
            item["housenumber"] = location["location"]["map_pin"].get("street_number")
            item["street"] = location["location"]["map_pin"].get("street_name")
            item["city"] = location["location"]["map_pin"]["city"]
            item["state"] = location["location"]["map_pin"].get(
                "state_short", location["location"]["map_pin"].get("state")
            )
            item["postcode"] = location["location"]["map_pin"]["post_code"]
            item["country"] = location["location"]["map_pin"]["country_short"]
            item["opening_hours"] = OpeningHours()
            for day, time in location["location"]["opening_hours"].items():
                if " - " in time:
                    item["opening_hours"].add_range(day, *time.split(" - "), time_format="%I:%M%p")

            yield item
