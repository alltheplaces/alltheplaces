from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class VinniesAUSpider(Spider):
    name = "vinnies_au"
    item_attributes = {"brand": "Vinnies", "brand_wikidata": "Q117547405", "extras": Categories.SHOP_CHARITY.value}
    allowed_domains = ["cms.vinnies.org.au"]
    start_urls = ["https://cms.vinnies.org.au/api/shops/get"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json():
            item = DictParser.parse(location)
            item["addr_full"] = location["fullAddress"]
            item["opening_hours"] = OpeningHours()
            for day in location["openingTimes"]:
                if day["closed"] or not day["open"] or not day["close"]:
                    continue
                item["opening_hours"].add_range(
                    day["weekday"], day["open"].split("T", 1)[1], day["close"].split("T", 1)[1], "%H:%M:%S"
                )
            yield item
