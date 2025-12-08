import json

from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.pipelines.address_clean_up import clean_address


class GullNZSpider(Spider):
    name = "gull_nz"
    item_attributes = {"brand": "Gull", "brand_wikidata": "Q111949119"}
    start_urls = ["https://gull.nz/find-a-gull/"]

    def parse(self, response, **kwargs):
        locations = json.loads(response.xpath("//@data-station").get())
        for location in locations:
            item = DictParser.parse(location)
            item["ref"] = str(location["location_id"])
            item["street_address"] = clean_address([location["addr1"], location["addr2"]])
            item["city"] = location["addr3"]
            item["postcode"] = location["addr4"]
            item["name"] = location["label"]

            if location["tradingHours"] == "24/7":
                item["opening_hours"] = "24/7"

            apply_yes_no(Extras.ATM, item, "ATM machine" in location["list"])
            apply_yes_no(Extras.COMPRESSED_AIR, item, "Air" in location["list"])
            apply_yes_no(Extras.TOILETS, item, "Bathroom facilities" in location["list"])
            apply_yes_no(Extras.CAR_WASH, item, "Car wash" in location["list"])
            apply_yes_no(Fuel.DIESEL, item, "Diesel" in location["list"])
            # "Force 10 (98 Octane, biofuel)"
            # "High-flow diesel"
            apply_yes_no(Fuel.LPG, item, "LPG fill" in location["list"] or "LPG swap" in location["list"])
            # "Pay-at-pump"
            apply_yes_no(Fuel.OCTANE_95, item, "Premium 95" in location["list"])
            apply_yes_no(Fuel.OCTANE_91, item, "Regular 91" in location["list"])
            # "Vouchers accepted"

            if "Boats only" in location["list"]:
                apply_category(Categories.BOAT_FUEL_STATION, item)
                item["nsi_id"] = "-1"  # Skip NSI matching
            else:
                apply_category(Categories.FUEL_STATION, item)

            yield item
