from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import DAYS_EN, OpeningHours


class FreedomFurnitureSpider(Spider):
    name = "freedom_furniture"
    item_attributes = {"brand": "Freedom", "brand_wikidata": "Q5500546"}
    allowed_domains = ["api-prod.freedom.com.au"]
    start_urls = [
        "https://api-prod.freedom.com.au/greenlitrest/v2/freedomfurniture/stores/country/AU?fields=FULL&lang=en&curr=AUD",
        "https://api-prod.freedom.com.au/greenlitrest/v2/freedomnewzealand/stores/country/NZ?fields=FULL&lang=en&curr=NZD",
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse)

    def parse(self, response):
        for location in response.json()["pointOfServices"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item.pop("name")
            item["branch"] = location["displayName"]
            if item["country"] == "NZ":
                item.pop("state")
                item["website"] = "https://www.freedomfurniture.co.nz/store-finder/stores/" + item["ref"]
            elif item["country"] == "AU":
                item["state"] = location["region"]["name"]
                item["website"] = "https://www.freedom.com.au/store-finder/stores/" + item["ref"]

            if "openingHours" in location:
                oh = OpeningHours()
                for day in location["openingHours"]["weekDayOpeningList"]:
                    if day["closed"]:
                        continue
                    open_time = day["openingTime"]["formattedHour"].upper()
                    if ":" not in open_time:
                        open_time = open_time.replace(" AM", ":00 AM").replace(" PM", ":00 PM")
                    close_time = day["closingTime"]["formattedHour"].upper()
                    if ":" not in close_time:
                        close_time = close_time.replace(" AM", ":00 AM").replace(" PM", ":00 PM")
                    oh.add_range(DAYS_EN[day["weekDay"]], open_time, close_time, "%I:%M %p")
                item["opening_hours"] = oh.as_opening_hours()

            yield item
