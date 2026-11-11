from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range


class IsmashGBSpider(Spider):
    name = "ismash_gb"
    item_attributes = {"brand": "iSmash", "name": "iSmash", "brand_wikidata": "Q42306824"}
    start_urls = ["https://ismash-api.eu.assurant.com/api/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            if location["isStore"] != 1:
                continue
            item = DictParser.parse(location)
            item["extras"]["ref:google:place_id"] = location["googleID"]
            item["branch"] = item.pop("name", None)
            if location["yelpID"]:
                item["extras"]["contact:yelp"] = urljoin("https://www.yelp.co.uk/biz/", location["yelpID"])

            apply_category(Categories.CRAFT_ELECTRONICS_REPAIR, item)

            item["opening_hours"] = OpeningHours()
            for day_info in ["mon_fri", "sat", "sun"]:
                days = day_range(*day_info.split("_")) if "_" in day_info else [day_info]
                hours_info = location.get(day_info) or ""
                if "-" in hours_info:
                    item["opening_hours"].add_days_range(days, *location[day_info].split("-"))
                elif "Closed" in hours_info.title():
                    item["opening_hours"].set_closed(days)
            yield item
