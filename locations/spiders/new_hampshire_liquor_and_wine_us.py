from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class NewHampshireLiquorAndWineUSSpider(Spider):
    name = "new_hampshire_liquor_and_wine_us"
    item_attributes = {"brand": "New Hampshire Liquor & Wine Outlets", "brand_wikidata": "Q98400557"}
    start_urls = ["https://www.liquorandwineoutlets.com/api/checkout/carts_storelist"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url, callback=self.parse)

    def parse(self, response):
        for location in response.json()["value"]:
            item = DictParser.parse(location)
            item["lat"] = location["Coords"]["Latitude"]
            item["lon"] = location["Coords"]["Longitude"]
            if "Designation" in location:
                for feature in location["Designation"]:
                    # {'AttributeId': 264182704991911, 'Name': 'Specialty Wine Stores', 'Value': '1', 'sort': 4}
                    # {'AttributeId': 151459076223870, 'Name': 'Specialty Spirits Stores', 'Value': '1', 'sort': 5}
                    if feature["Name"] == "ATM on the premises":
                        apply_yes_no(Extras.ATM, item, feature["Value"] == "1")

            item["opening_hours"] = OpeningHours()
            for day in location["ExtendedFields"]:
                item["opening_hours"].add_range(
                    day["DayOfTheWeek"], day["OpenTime"].replace(" ", ""), day["CloseTime"].replace(" ", ""), "%H:%M%p"
                )

            yield item
