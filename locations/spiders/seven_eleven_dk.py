import re

from scrapy import Spider

from locations.categories import Categories, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS_DK, OpeningHours, day_range, sanitise_day


class SevenElevenDKSpider(Spider):
    name = "seven_eleven_dk"
    item_attributes = {"brand": "7-Eleven", "brand_wikidata": "Q259340"}
    start_urls = ["https://www.7-eleven.dk/wp-content/themes/7-eleven/get_stores.php"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = location.pop("address")

            item = DictParser.parse(location)

            item["ref"] = item["website"] = location["smiley"]

            item["opening_hours"] = OpeningHours()
            for rule in location["open"].replace("24.00", "23.59").split(";"):
                if match := re.match(r"(\w+)(?:\-(\w+))?: (\d\d\.\d\d)\-(\d\d\.\d\d)", rule):
                    start_day, end_day, start_time, end_time = match.groups()
                    start_day = sanitise_day(start_day, DAYS_DK)
                    end_day = sanitise_day(end_day, DAYS_DK)
                    if start_day:
                        if not end_day:
                            end_day = start_day
                        for day in day_range(start_day, end_day):
                            item["opening_hours"].add_range(day, start_time, end_time, time_format="%H.%M")

            if location["type"] == "shell":
                apply_category(Categories.FUEL_STATION, item)
                apply_yes_no("car_wash", item, location["carwash"] == "on")
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
