from scrapy import Spider

from locations.dict_parser import DictParser
from locations.categories import Categories, apply_category, apply_yes_no



class NouriaUSSpider(Spider):
    name = "nouria_us"
    start_urls = ["https://nouria.com/wp-json/nouria/v1/locations"]
    item_attributes = {"brand": "Nouria", "brand_wikidata": "Q120637476"}

    def parse(self, response):
        for location in response.json():
            location = location | location["address"]
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["website"] = location["link"]
            item["street_address"] = location["address"]["address_line_1"]
            if location["address"]["address_line_2"]:
                item["street_address"] += " " + location["address"]["address_line_2"]

            # every location is a convenience store but not every location has a Nouria branded gas station
            apply_category(Categories.SHOP_CONVENIENCE, item)
            if "nouria-fuel" in location["filters"]:
                apply_category(Categories.FUEL_STATION, item)

            apply_yes_no("sells:alcohol", item, "beer-wine" in location["filters"])
            yield item
        
