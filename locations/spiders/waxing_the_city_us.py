from scrapy import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.spiders.vapestore_gb import clean_address


class WaxingTheCityUSSpider(Spider):
    name = "waxing_the_city_us"
    item_attributes = {"brand": "Waxing the City", "brand_wikidata": "Q120599883"}
    start_urls = ["https://www.waxingthecity.com/wp-json/anytime/v1/map-locations"]

    def parse(self, response, **kwargs):
        for location in response.json():
            location.update(location.pop("content"))
            location["street_address"] = clean_address([location.pop("address"), location.pop("address2")])

            item = DictParser.parse(location)
            item["ref"] = location["number"]

            item["opening_hours"] = OpeningHours()
            for rule in location["hours"]:
                item["opening_hours"].add_range(
                    rule["dayOfWeek"], rule["openTime"], rule["closeTime"], time_format="%H%M"
                )

            yield item
