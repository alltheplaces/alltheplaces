import csv
from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours

GREAT_WALL_MOTOR_SHARED_ATTRIBBUTES = {"brand": "GWM", "brand_wikidata": "Q1117001"}


class GreatWallMotorAUNZSpider(Spider):
    name = "great_wall_motor_au_nz"
    item_attributes = GREAT_WALL_MOTOR_SHARED_ATTRIBBUTES
    allowed_domains = ["api.storyblok.com", "a.storyblok.com"]
    start_urls = [
        "https://api.storyblok.com/v2/cdn/stories/dealer-locator?cv=1715928712&language=au&resolve_relations=SelectModelLine.options%2CSelectEnquiryType.options&token=grBrbRuRX6NJLbQcyDGpcgtt&version=published"
    ]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        locations_csv_url = response.json()["story"]["content"]["body"][0]["stores"]["filename"]
        yield Request(url=locations_csv_url, callback=self.parse_locations)

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        reader = csv.DictReader(response.text.splitlines())
        for location in reader:
            item = DictParser.parse(location)
            item["ref"] = location["Dealer code"]
            item["name"] = location["Dealer Name"]
            item["street_address"] = item.pop("addr_full", None)
            if location["Country"] != "NZ":
                item["state"] = location["State/Region"]
            item["postcode"] = location["Post Code"]
            item["opening_hours"] = OpeningHours()
            for day_name in DAYS_FULL:
                if day_hours := location.get(day_name):
                    if day_hours == "Closed":
                        item["opening_hours"].set_closed(day_name)
                    elif " - " in day_hours:
                        open_time, close_time = day_hours.split(" - ", 1)
                        if close_time == "12:00 AM":
                            close_time = "12:00 PM"
                        item["opening_hours"].add_range(day_name, open_time, close_time, "%I:%M %p")
            apply_category(Categories.SHOP_CAR, item)
            yield item
