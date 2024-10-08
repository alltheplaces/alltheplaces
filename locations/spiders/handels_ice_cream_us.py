import json

from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_FULL, OpeningHours


class HandelsIceCreamUSSpider(Spider):
    name = "handels_ice_cream_us"
    item_attributes = {"brand": "Handel's Homemade Ice Cream", "brand_wikidata": "Q16983222"}
    start_urls = ["https://handelsicecream.com/"]

    def parse(self, response):
        js = response.xpath("//script[contains(text(), 'var branches =')]/text()").get()
        for location in json.loads(js[js.find("=") + 1 : js.rfind(";")]).values():
            item = DictParser.parse(location)
            item["addr_full"] = location["address"].replace("<br>", ", ")
            item["branch"] = item.pop("name")
            item["website"] = location["link"]

            oh = OpeningHours()
            for day in DAYS_FULL:
                oh.add_ranges_from_string(f"{day} {location[day.lower()]}")
            item["opening_hours"] = oh

            yield item
