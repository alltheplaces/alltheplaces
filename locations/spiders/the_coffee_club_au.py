from scrapy import Spider
from scrapy.http import JsonRequest

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import clean_address


class TheCoffeeClubAUSpider(Spider):
    name = "the_coffee_club_au"
    item_attributes = {"brand": "The Coffee Club", "brand_wikidata": "Q7726599"}
    allowed_domains = ["api.mdkl.com.au"]
    states_list = ["ACT", "NSW", "NT", "QLD", "SA", "TAS", "VIC", "WA"]

    def start_requests(self):
        for state in self.states_list:
            yield JsonRequest(
                url=f"https://api.mdkl.com.au/v1/Stores/GetByCountryAndState?brandId=TCC&country=Australia&stateAbr={state}"
            )

    def parse(self, response):
        for location in response.json():
            if not location["open"]:
                continue
            item = DictParser.parse(location)
            item["ref"] = location["storeNumber"]
            item["street_address"] = clean_address([location["addressLine1"], location["addressLine2"]])
            item["website"] = "https://coffeeclub.com.au/pages/store-details?country=Australia&name=" + location[
                "displayName"
            ].lower().replace(" ", "-")
            item["opening_hours"] = OpeningHours()
            for day_hours in location["openingHours"]:
                if day_hours["closed"]:
                    continue
                item["opening_hours"].add_range(
                    day_hours["dayName"],
                    day_hours["displayHours"].split(" - ", 1)[0],
                    day_hours["displayHours"].split(" - ", 1)[1],
                    "%I:%M %p",
                )
            yield item
