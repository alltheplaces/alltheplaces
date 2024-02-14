import re

import chompjs
import scrapy

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range
from locations.spiders.vapestore_gb import clean_address


class TheFreshGrocerSpider(scrapy.Spider):
    name = "the_fresh_grocer_us"
    item_attributes = {
        "brand": "The Fresh Grocer",
        "brand_wikidata": "Q18389721",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    start_urls = ["https://www.thefreshgrocer.com/"]
    requires_proxy = True

    def parse(self, response, **kwargs):
        for location in chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "__PRELOADED_STATE__")]/text()').get()
        )["stores"]["availablePlanningStores"]["items"]:
            location["street_address"] = clean_address(
                [location["addressLine1"], location["addressLine2"], location["addressLine3"]]
            )
            location["state"] = location["countyProvinceState"]
            item = DictParser.parse(location)
            item["ref"] = location["retailerStoreId"]
            item["website"] = f'https://www.thefreshgrocer.com/sm/planning/rsid/{item["ref"]}'

            if m := re.search(
                r"(\w+)(?: (?:-|thru) (\w+))?: (\d+)\s*([ap]m) (?:-|to) (\d+)\s*([ap]m)",
                location["openingHours"],
                re.IGNORECASE,
            ):
                start_day, end_day, start_time, start_zone, end_time, end_zone = m.groups()
                if not end_day:
                    end_day = start_day
                if start_day and end_day:
                    item["opening_hours"] = OpeningHours()
                    item["opening_hours"].add_days_range(
                        day_range(start_day, end_day),
                        f"{start_time}{start_zone}",
                        f"{end_time}{end_zone}",
                        time_format="%I%p",
                    )

            yield item
