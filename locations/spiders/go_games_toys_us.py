from typing import Any

import scrapy
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class GoGamesToysUSSpider(scrapy.Spider):
    name = "go_games_toys_us"
    item_attributes = {
        "brand_wikidata": "Q108312837",
        "brand": "Go! Games & Toys",
    }
    allowed_domains = [
        "goretailgroup.com",
    ]
    start_urls = [
        "https://www.goretailgroup.com/api/getStoreLocator?startIndex=1&filter=geo%20near(40.75368539999999,-73.999163)&pageSize=1000&radius=10000"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["items"]["items"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            if item["name"] == "Attic Salt":
                item["brand"] = "Attic Salt"
                item["brand_wikidata"] = "Q108409773"
            item["ref"] = location["code"]
            item["city"] = location["cityOrTown"]
            item["state"] = location["stateOrProvince"]
            item["postcode"] = location["postalOrZipCode"]
            item["street_address"] = merge_address_lines([location["address2"], item["street_address"]])
            apply_category(Categories.SHOP_TOYS, item)
            item["opening_hours"] = OpeningHours()
            for day, time in location["regularHours"].items():
                open_time, close_time = time["label"].split(" - ")
                item["opening_hours"].add_range(
                    day=day, open_time=open_time, close_time=close_time, time_format="%I %p"
                )
            # "name" field contains:
            #   - "Attic Salt"
            #   - "Go! Games & Toys"
            #   - "Go! Calendars Games & Toys"
            #   - "Go! Calendars, Games and Toys"
            #   - "Go!CalendarsGamesToys&Books"
            #   - etc
            # Due to the inconsistencies, we'll just drop the field completely
            # so that the "brand" value is used instead. There is no branch name
            # to extract from the "name" field.
            item.pop("name", None)
            yield item
