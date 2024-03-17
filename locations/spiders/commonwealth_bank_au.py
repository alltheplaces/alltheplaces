from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class CommonwealthBankAUSpider(Spider):
    name = "commonwealth_bank_au"
    item_attributes = {"brand": "Commonwealth Bank", "brand_wikidata": "Q285328"}

    def start_requests(self):
        for city in city_locations("AU", 1500):
            yield JsonRequest(
                f'https://www.commbank.com.au/digital/locate-us/api/branches/findByLocation?location={city["latitude"]},{city["longitude"]}&top=1000',
                callback=self.parse_banks,
            )
            yield JsonRequest(
                f'https://www.commbank.com.au/digital/locate-us/api/atms/findByLocation?location={city["latitude"]},{city["longitude"]}&top=1000',
                callback=self.parse_atms,
            )

    def parse_atms(self, response, **kwargs):
        for location in response.json():
            for atm in location["atmList"]:
                atm["street_address"] = merge_address_lines([atm.pop("street1"), atm.pop("street2")])
                item = DictParser.parse(atm)
                item["name"] = atm["siteName"]
                item["ref"] = atm["atmId"]

                apply_category(Categories.ATM, item)

                yield item

    def parse_banks(self, response, **kwargs):
        for location in response.json():
            location["street_address"] = merge_address_lines([location.pop("street1"), location.pop("street2")])
            item = DictParser.parse(location)
            item["city"] = location["suburb"]

            item["opening_hours"] = OpeningHours()
            for day in location["operationDays"]:
                item["opening_hours"].add_range(day["daysOfWeek"], day["open"], day["close"], time_format="%I:%M %p")

            apply_category(Categories.BANK, item)

            yield item
