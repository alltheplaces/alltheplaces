import json
import re

import scrapy

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class QualityDairyUSSpider(scrapy.Spider):
    name = "qualitydairy_us"
    item_attributes = {"brand": "Quality Dairy", "brand_wikidata": "Q23461886"}
    start_urls = ["https://qualitydairy.com/v15/stores/"]
    requires_proxy = True

    def parse(self, response, **kwargs):
        for location in json.loads(re.search("qd_locations = (.*);", response.text).group(1)):
            location["url"] = location["url"]  # .replace("http://", "https://")
            yield scrapy.Request(
                location["url"],
                cb_kwargs={"location": location},
                callback=self.parse_location,
            )

    def parse_location(self, response, location, **kwargs):
        location["street_address"] = merge_address_lines([location.pop("address"), location.pop("address2")])
        item = DictParser.parse(location)

        item["opening_hours"] = OpeningHours()
        for rule in response.xpath('//table[@id="hours-table"]//tr'):
            day, start_time, _, end_time = rule.xpath("./td/text()").getall()
            item["opening_hours"].add_range(
                day, self.clean_time(start_time), self.clean_time(end_time), time_format="%I:%M %p"
            )

        yield item

    @staticmethod
    def clean_time(time: str) -> str:
        # "6 a.m." or "5:00am" or "11 p,m." to "5:00 am"
        time = time.replace(".", "").replace(",", "")
        timezone = time[-2:]
        time = time[:-2].strip()

        if ":" not in time:
            time += ":00"

        return f"{time} {timezone}"
