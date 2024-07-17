from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NinetyNineRanchMarketUSSpider(Spider):
    name = "99_ranch_market_us"
    item_attributes = {
        "brand": "99 Ranch Market",
        "brand_wikidata": "Q4646307",
        "extras": Categories.SHOP_SUPERMARKET.value,
    }
    allowed_domains = ["api.awsprod.99ranch.com"]
    start_urls = ["https://api.awsprod.99ranch.com/store/web/nearby/stores"]

    def start_requests(self):
        data = {
            "address": "Foster City, CA, USA",
            "zipCode": "",
            "longitude": -122.2710788,
            "latitude": 37.5585465,
            "pageSize": 1000,
            "pageNum": 1,
            "type": 1,
            "source": "WEB",
            "within": 10000,
        }
        yield JsonRequest(url=self.start_urls[0], data=data, method="POST")

    def parse(self, response):
        for location in response.json()["data"]["records"]:
            item = DictParser.parse(location)
            item.pop("email", None)
            item["image"] = location.get("logo")

            hours_string = ""
            for day_hours in location.get("offlineBusinessTimes", []):
                hours_string = "{} {}: {} - {}".format(
                    hours_string, day_hours["dayOfWeeks"], day_hours["startTime"], day_hours["endTime"]
                )
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
