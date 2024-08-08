from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class Rema1000NOSpider(Spider):
    name = "rema_1000_no"
    item_attributes = {"brand": "REMA 1000", "brand_wikidata": "Q28459", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.rema.no"]
    start_urls = ["https://www.rema.no/wp-json/rema-stores/v1/get-stores-data"]

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item.pop("website", None)
            item["street_address"] = location.get("visitAddress")
            item["city"] = location.get("visitPlaceName")
            item["postcode"] = location.get("visitPostCode")
            item["state"] = location.get("countyName")

            hours_string = ""
            for day_name, day_hours in location.get("openingHours", {}).items():
                hours_string = "{} {}: {}".format(hours_string, day_name, day_hours)
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string)

            yield item
