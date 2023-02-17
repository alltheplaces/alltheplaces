import json

from scrapy import Spider

from locations.categories import Fuel, apply_yes_no
from locations.dict_parser import DictParser


class GullNZSpider(Spider):
    name = "gull_nz"
    item_attributes = {"brand_wikidata": "Q111949119"}
    start_urls = ["https://gull.nz/find-a-gull/"]

    def parse(self, response, **kwargs):
        locations = json.loads(response.xpath("//@data-station").get())
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = str(location["location_id"])
            item["street_address"] = ", ".join(filter(None, [location["addr1"], location["addr2"]]))
            item["city"] = location["addr3"]
            item["postcode"] = location["addr4"]
            item["name"] = location["label"]

            if location["tradingHours"] == "24/7":
                item["opening_hours"] = "24/7"

            apply_yes_no(Fuel.OCTANE_91, item, "Regular 91" in location["list"])
            apply_yes_no(Fuel.DIESEL, item, "Diesel" in location["list"])
            apply_yes_no(Fuel.OCTANE_95, item, "Premium 95" in location["list"])

            yield item
