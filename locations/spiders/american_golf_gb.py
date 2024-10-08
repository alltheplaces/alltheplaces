from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class AmericanGolfGBSpider(Spider):
    name = "american_golf_gb"
    item_attributes = {"brand": "American Golf", "brand_wikidata": "Q62657494"}
    custom_settings = {"ROBOTSTXT_OBEY": False}
    start_urls = [
        "https://www.americangolf.co.uk/on/demandware.store/Sites-AmericanGolf-GB-Site/en_GB/Stores-GetAllStores"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["street_address"] = merge_address_lines([location["address1"], location["address2"]])
            item["website"] = response.urljoin(location["detailsLink"])

            if location.get("storeHours"):
                item["opening_hours"] = OpeningHours()
                for day in map(str.lower, DAYS_FULL):
                    try:
                        day_hours = location["storeHours"][day].strip()
                        if "CLOSED" in day_hours.upper():
                            item["opening_hours"].set_closed(day)
                        else:
                            item["opening_hours"].add_range(day, *day_hours.split(" - "))
                    except:
                        continue

            yield item
