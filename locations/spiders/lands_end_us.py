import re

import scrapy
import xmltodict

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range, sanitise_day
from locations.user_agents import BROWSER_DEFAULT


class LandsEndUSSpider(scrapy.Spider):
    name = "lands_end_us"
    item_attributes = {"brand": "Lands' End", "brand_wikidata": "Q839555", "extras": Categories.SHOP_CLOTHES.value}
    start_urls = [
        "https://www.landsend.com/pp/StoreLocator?lat=42.7456634&lng=-90.4879916&radius=3000&S=S&L=L&C=undefined&N=N"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}
    user_agent = BROWSER_DEFAULT

    def parse(self, response, **kwargs):
        for xml_location in xmltodict.parse(response.text)["markers"]["marker"]:
            # strip "@" prefix
            location = {}
            for k, v in xml_location.items():
                location[k.replace("@", "")] = v

            location["ref"] = location.pop("storenumber")
            location["street_address"] = location.pop("address")

            item = DictParser.parse(location)

            item["opening_hours"] = OpeningHours()
            for start_day, end_day, start_hour, start_tz, end_hour, end_tz in re.findall(
                r"(\w+)(?:\s*-\s*(\w+))?:\s*(\d+)(am|pm)\s*-\s*(\d+)(am|pm)", location.get("storehours")
            ):
                start_day = sanitise_day(start_day)
                end_day = sanitise_day(end_day)
                if not end_day:
                    end_day = start_day

                if start_day and end_day:
                    item["opening_hours"].add_days_range(
                        day_range(start_day, end_day),
                        f"{start_hour}{start_tz}",
                        f"{end_hour}{end_tz}",
                        time_format="%I%p",
                    )

            yield item
