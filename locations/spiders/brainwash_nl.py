from typing import Iterable

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class BrainwashNLSpider(Spider):
    name = "brainwash_nl"
    item_attributes = {"brand": "BrainWash", "brand_wikidata": "Q114905133"}
    allowed_domains = ["www.brainwash-kappers.nl"]
    start_urls = ["https://www.brainwash-kappers.nl/salons/"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response) -> Iterable[Feature]:
        for salon in chompjs.parse_js_object(
            chompjs.parse_js_object(response.xpath('//*[contains(text(),"postalCode")]/text()').get())[1]
        )[3]["salons"]:
            item = DictParser.parse(salon)
            item["website"] = "https://www.brainwash-kappers.nl/salons/" + salon["slug"]
            oh = OpeningHours()
            for day_time in salon["openingTimes"]:
                day = day_time["day"]
                open_time = day_time["from"].replace(".000", "")
                close_time = day_time["till"].replace(".000", "")
                oh.add_range(day=day, open_time=open_time, close_time=close_time, time_format="%H:%M:%S")
            item["opening_hours"] = oh
            yield item
