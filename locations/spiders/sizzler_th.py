import scrapy
from scrapy.http import Request

from locations.dict_parser import DictParser
from locations.user_agents import BROWSER_DEFAULT


class SizzlerTHSpider(scrapy.Spider):
    name = "sizzler_th"
    item_attributes = {
        "brand": "Sizzler",
        "brand_wikidata": "Q1848822",
    }
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def start_requests(self):
        yield Request(url="https://www.sizzler.co.th/api/search/location?location=&province=&lang=en")

    def parse(self, response):
        locations = response.json()
        if len(locations) > 0:
            for location in locations:
                item = DictParser.parse(location)
                item["addr_full"] = location.get("address_th")
                item["extras"]["addr:full:en"] = location.get("address_en")
                item["extras"]["check_date"] = location.get("updated_at")

                yield item
