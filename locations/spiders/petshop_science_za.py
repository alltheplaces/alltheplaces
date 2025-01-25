from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class PetshopScienceZASpider(Spider):
    name = "petshop_science_za"
    item_attributes = {"brand": "Petshop Science", "brand_wikidata": "Q129202801"}
    start_urls = [
        "https://www.petshopscience.co.za/occ/v2/petshopscience/stores?fields=stores(name%2CdisplayName%2CformattedDistance%2CopeningHours(weekDayOpeningList(FULL)%2CspecialDayOpeningList(FULL))%2CgeoPoint(latitude%2Clongitude)%2Caddress(line1%2Cline2%2Ctown%2Cregion(FULL)%2CpostalCode%2Cphone%2Ccountry%2Cemail)%2C%20features)%2Cpagination(DEFAULT)%2Csorts(DEFAULT)&query=&pageSize=-1&lang=en&curr=ZAR&region=PSS_70857"
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            if state := item.get("state"):
                item["state"] = state
            item["website"] = "https://www.petshopscience.co.za/store-finder/country/ZA/" + location["name"]
            if "openingHours" in location:
                item["opening_hours"] = OpeningHours()
                for day in location["openingHours"]["weekDayOpeningList"]:
                    if day["closed"]:
                        item["opening_hours"].set_closed(day["weekDay"])
                    else:
                        item["opening_hours"].add_range(
                            day["weekDay"],
                            day["openingTime"]["formattedHour"].upper(),
                            day["closingTime"]["formattedHour"].upper(),
                            "%I:%M %p",
                        )
            yield item
