from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


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
            item = DictParser.parse(location)
            item["ref"] = item.pop("name")
            item["branch"] = location["displayName"]
            item["street_address"] = clean_address([location["address"].get("line1"), location["address"].get("line2")])
            item["city"] = location["address"].get("town")
            try:
                item["state"] = location["address"].get("region").get("name")
            except:
                pass
            item["postcode"] = location["address"].get("postalCode")
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")
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
