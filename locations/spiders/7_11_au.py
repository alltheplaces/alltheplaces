import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class SevenElevenAUSpider(scrapy.Spider):
    name = "seven_eleven_au"
    item_attributes = {"brand": "7-Eleven", "brand_wikidata": "Q259340"}
    start_urls = ["https://www.7eleven.com.au/storelocator-retail/mulesoft/stores"]

    def parse(self, response, **kwargs):
        for location in response.json()["stores"]:
            location["address"]["street_address"] = ", ".join(
                filter(None, [location["address"].pop("address1"), location["address"].pop("address2")])
            )
            location["address"]["country_code"] = location["region"]["countryId"]
            item = DictParser.parse(location)

            item["lat"], item["lon"] = location["location"]

            item["opening_hours"] = OpeningHours()
            for rule in location["openingHours"]:
                item["opening_hours"].add_range(
                    DAYS[rule["day_of_week"] - 1], rule["start_time"], rule["end_time"], time_format="%I:%M %p"
                )

            apply_yes_no("atm", item, location["atm"])

            if location["isFuelStore"]:
                apply_category(Categories.FUEL_STATION, item)
                apply_yes_no(Fuel.DIESEL, item, "Diesel" in location["fuelOptions"])
                apply_yes_no(Fuel.E10, item, "E10" in location["fuelOptions"])
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
