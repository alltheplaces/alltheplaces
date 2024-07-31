from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class LiquorshopZASpider(Spider):
    name = "liquorshop_za"
    item_attributes = {"brand": "LiquorShop", "brand_wikidata": "Q5089126", "extras": Categories.SHOP_ALCOHOL.value}
    allowed_domains = ["www.liquorshop.co.za"]
    start_urls = [
        "https://www.liquorshop.co.za/occ/v2/liquorshop/stores?fields=stores(name%2CdisplayName%2CformattedDistance%2CopeningHours(weekDayOpeningList(FULL)%2CspecialDayOpeningList(FULL))%2CgeoPoint(latitude%2Clongitude)%2Caddress(line1%2Cline2%2Ctown%2Cregion(FULL)%2CpostalCode%2Cphone%2Ccountry%2Cemail)%2C%20features)%2Cpagination(DEFAULT)%2Csorts(DEFAULT)&query=&pageSize=-1&lang=en&curr=ZAR&region=ls_za"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["name"].replace("LS ", "").replace("LS", "").strip()
            item["name"] = location["displayName"]
            item["addr_full"] = ", ".join(
                filter(None, [location["address"].get("line1"), location["address"].get("line2")])
            )
            if location["address"].get("region"):
                item["state"] = location["address"]["region"]["name"]
            item["phone"] = location["address"].get("phone")
            item["website"] = "https://www.liquorshop.co.za/store-finder/country/ZA/" + item["ref"]
            item["opening_hours"] = OpeningHours()
            for day_hours in location["openingHours"]["weekDayOpeningList"]:
                if day_hours["closed"]:
                    continue
                item["opening_hours"].add_range(
                    day_hours["weekDay"],
                    day_hours["openingTime"]["formattedHour"],
                    day_hours["closingTime"]["formattedHour"],
                    "%I:%M %p",
                )
            yield item
