import re

import chompjs
import scrapy

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class BanqueMisrEGSpider(scrapy.Spider):
    name = "banque_misr_eg"
    item_attributes = {"brand": "Banque Misr", "brand_wikidata": "Q2060638"}
    start_urls = ["https://www.banquemisr.com/Home/ABOUT%20US/Locations?sc_lang=en"]

    def parse(self, response, **kwargs):
        cities = chompjs.parse_js_object(
            response.xpath('//script[contains(text(), "countriesJson")]/text()').re_first(
                r"countriesJson\s*=\s*\'(\[.+\])\'"
            )
        )
        for city in cities:
            yield scrapy.Request(
                url=f'https://www.banquemisr.com/api/sitecore/LocationsApi/GetPlaces?GovernateId={city["id"]}&IsBranch=true&IsAtm=true&lang=en',
                callback=self.parse_locations,
                cb_kwargs=dict(city=city["name"]),
            )

    def parse_locations(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["city"] = kwargs["city"]
            if phones := location.get("phones"):
                item["phone"] = phones[0].replace(" - ", ";") if phones[0] not in ["0", "", " "] else None
            item["opening_hours"] = OpeningHours()
            if not any([day in location["WorkingHours"] for day in DAYS_FULL]):
                for start_time, start_format, end_time, end_format in re.findall(
                    r"(\d+:\d+)\s*(AM|PM)\s*[-a-z]+\s*(\d+:\d+)\s*(AM|PM)",
                    location["WorkingHours"].replace("24 hours", "12:00 AM-11:59 PM"),
                    re.IGNORECASE,
                ):
                    open_time = f"{start_time} {start_format}"
                    close_time = f"{end_time} {end_format}"
                    item["opening_hours"].add_days_range(DAYS_FULL, open_time, close_time, time_format="%I:%M %p")
            else:
                item["opening_hours"].add_ranges_from_string(location["WorkingHours"])
            if location["isBranch"]:
                apply_category(Categories.BANK, item)
            else:
                apply_category(Categories.ATM, item)
            yield item
