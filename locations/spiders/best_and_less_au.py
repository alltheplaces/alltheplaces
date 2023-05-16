from urllib.parse import quote

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class BestAndLessAUSpider(Spider):
    name = "best_and_less_au"
    item_attributes = {"brand": "Best & Less", "brand_wikidata": "Q4896542"}
    allowed_domains = ["www.bestandless.com.au"]
    start_urls = [
        "https://www.bestandless.com.au/stores/ACT",
        "https://www.bestandless.com.au/stores/NSW",
        "https://www.bestandless.com.au/stores/NT",
        "https://www.bestandless.com.au/stores/QLD",
        "https://www.bestandless.com.au/stores/SA",
        "https://www.bestandless.com.au/stores/TAS",
        "https://www.bestandless.com.au/stores/VIC",
        "https://www.bestandless.com.au/stores/WA",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, method="POST")

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item.pop("housenumber")
            item.pop("street")
            item["street_address"] = ", ".join(filter(None, [location["address"]["line1"], location["address"]["line2"]]))
            item["addr_full"] = location["address"]["formattedAddress"]
            item["state"] = location["address"]["state"]
            item["phone"] = location["address"]["phone"]
            item["email"] = location["address"]["email"]
            item["website"] = "https://www.bestandless.com.au" + quote(location["url"])
            item["opening_hours"] = OpeningHours()
            for day in location["openingHours"]["weekDayOpeningList"]:
                if day["closed"]:
                    continue
                item["opening_hours"].add_range(day["weekDay"], day["openingTime"]["formattedHour"].upper(), day["closingTime"]["formattedHour"].upper(), "%I:%M %p")
            yield item
