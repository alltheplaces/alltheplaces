import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class BathAndBodyWorksUSSpider(scrapy.Spider):
    name = "bath_and_body_works_us"
    item_attributes = {"brand": "Bath & Body Works", "brand_wikidata": "Q810773"}
    allowed_domains = ["bathandbodyworks.com"]
    start_urls = [
        "https://www.bathandbodyworks.com/on/demandware.store/Sites-BathAndBodyWorks-Site/en_US/Stores-GetNearestStores?latitude=45&longitude=-120&countryCode=US&distanceUnit=mi&maxdistance=25000&BBW=1&BBWO=1"
    ]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response, **kwargs):
        for ref, store in response.json()["stores"].items():
            store["street_address"] = clean_address([store.pop("address1"), store.pop("address2")])
            item = DictParser.parse(store)
            item["ref"] = ref

            oh = OpeningHours()
            for day, start_hour, start_minutes, start_am_pm, end_hour, end_minutes, end_am_pm in re.findall(
                r"(\w+): (\d+):?(\d+)?(AM|PM)-(\d+):?(\d+)?(AM|PM)", store["storeHours"]
            ):
                oh.add_range(
                    day,
                    f'{start_hour.zfill(2)}:{start_minutes or "00"} {start_am_pm}',
                    f'{end_hour.zfill(2)}:{end_minutes or "00"} {end_am_pm}',
                    time_format="%I:%M %p",
                )
            item["opening_hours"] = oh.as_opening_hours()

            yield item
