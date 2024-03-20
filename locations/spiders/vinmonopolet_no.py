from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import DAYS_NO, OpeningHours


class VinmonopoletNOSpider(Spider):
    name = "vinmonopolet_no"
    item_attributes = {"brand": "Vinmonopolet", "brand_wikidata": "Q1740534", "extras": Categories.SHOP_ALCOHOL.value}
    allowed_domains = ["www.vinmonopolet.no"]
    start_urls = ["https://www.vinmonopolet.no/vmpws/v2/vmp/stores/?fields=FULL&pageSize=1000"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location.get("name")
            item["name"] = location.get("displayName")
            item["addr_full"] = location["address"].get("formattedAddress")
            item["website"] = "https://www.vinmonopolet.no/butikk/" + item["ref"]
            item["phone"] = location["address"].get("phone")

            item["opening_hours"] = OpeningHours()
            for day_hours in location.get("openingTimes"):
                if day_hours["closed"]:
                    continue
                item["opening_hours"].add_range(
                    DAYS_NO[day_hours["weekDay"]],
                    day_hours["openingTime"]["formattedHour"],
                    day_hours["closingTime"]["formattedHour"],
                )

            yield item
