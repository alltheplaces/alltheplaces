import scrapy

from locations.categories import Extras, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.pipelines.address_clean_up import merge_address_lines


class RedLobsterUSSpider(scrapy.Spider):
    name = "redlobster_us"
    item_attributes = {"brand": "Red Lobster", "brand_wikidata": "Q846301", "country": "US"}
    start_urls = ["https://www.redlobster.com/api/location/GetLocations?latitude=0&longitude=0&radius=150000"]

    @staticmethod
    def parse_hours(hours: [dict]) -> OpeningHours:
        oh = OpeningHours()

        for rule in hours:
            oh.add_range(DAYS[rule["dayOfWeek"]], rule["open"], rule["close"], time_format="%I:%M %p")

        return oh

    def parse(self, response, **kwargs):
        for location in response.json()["locations"]:
            location = location["location"]
            location["street_address"] = merge_address_lines([location.pop("address1"), location.pop("address2")])
            item = DictParser.parse(location)
            item["ref"] = location["restaurantNumber"]
            item["opening_hours"] = self.parse_hours(location["hours"])
            item["website"] = f'https://www.redlobster.com/locations/list/{location["localPageURL"]}'

            apply_yes_no(Extras.DELIVERY, item, location["hasDelivery"])

            yield item
