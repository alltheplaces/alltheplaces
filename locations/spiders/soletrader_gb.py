import json
import re
from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, DAYS_FULL, OpeningHours
from locations.items import Feature


class SoletraderGBSpider(Spider):
    name = "soletrader_gb"
    item_attributes = {"brand": "Soletrader", "brand_wikidata": "Q25101942", "extras": Categories.SHOP_SHOES.value}
    start_urls = ["https://www.soletrader.co.uk/store-locator"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.xpath('//script[contains(text(),"postalCode")]/text()').get()
        data = re.sub(r'\\"', '"', data)
        data = re.sub(r'^.*locations":', "", data)
        data = re.sub(r'\}\]\\n"\]\)$', "", data)
        for location in json.loads(data):
            item = Feature()
            address = location["address"]
            item = DictParser.parse(address)
            item["street_address"] = address["address2"]
            item["name"] = address["address1"]
            item["ref"] = location["entityId"]

            oh = OpeningHours()
            for day in DAYS_FULL:
                open_time = location["operatingHours"][day.lower()]["opening"]
                close_time = location["operatingHours"][day.lower()]["closing"]
                oh.add_range(
                    day=DAYS_EN[day],
                    open_time=open_time,
                    close_time=close_time,
                )

            item["opening_hours"] = oh.as_opening_hours()

            yield item
