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
        f"https://prodapi.bestandless.com.au/occ/v2/bnlsite/stores/location/{state}?fields=FULL"
        for state in ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["address"]["id"]
            item["addr_full"] = location["address"].get("formattedAddress")
            item["street_address"] = ", ".join(
                filter(None, [location["address"].get("line1"), location["address"].get("line2")])
            )
            item["city"] = location["address"].get("town")
            item["state"] = location["address"].get("state")
            item["postcode"] = location["address"].get("postalCode")
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")
            item["website"] = "https://www.bestandless.com.au" + quote(location["url"])
            item["opening_hours"] = OpeningHours()
            for day in location["openingHours"]["weekDayOpeningList"]:
                if day["closed"]:
                    continue
                item["opening_hours"].add_range(
                    day["weekDay"],
                    day["openingTime"]["formattedHour"].upper(),
                    day["closingTime"]["formattedHour"].upper(),
                    "%I:%M %p",
                )
            yield item
