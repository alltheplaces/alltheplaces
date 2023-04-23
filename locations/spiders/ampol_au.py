from scrapy import Spider

from locations.categories import apply_category, apply_yes_no, Categories, Fuel
from locations.hours import OpeningHours
from locations.dict_parser import DictParser


class AmpolAUSpider(Spider):
    name = "ampol_au"
    item_attributes = {"brand": "Ampol", "brand_wikidata": "Q4748528"}
    allowed_domains = ["www.ampol.com.au"]
    start_urls = ["https://www.ampol.com.au/custom/api/locator/get"]

    def parse(self, response):
        for location in response.json()["value"]:
            item = DictParser.parse(location)
            item["geometry"] = location["Location"]
            item["street_address"] = location["Address"]

            apply_category(Categories.FUEL_STATION, item)
            if location["Brand"] == "Eg Ampol":
                item["brand"] = "EG Ampol"
                apply_category(Categories.SHOP_CONVENIENCE, item)
            elif location["Brand"] == "The Foodary":
                item["brand"] = "Ampol Foodary"
                apply_category(Categories.SHOP_CONVENIENCE, item)

            item["opening_hours"] = OpeningHours()
            for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
                if location[f"{day}_AllDay"]:
                    item["opening_hours"].add_range(day, "00:00", "23:59")
                else:
                    item["opening_hours"].add_range(day, location[f"{day}_Openning"].replace("Midnight", "00:00"), location[f"{day}_Closing"].replace("Midnight", "23:59"))

            apply_yes_no(Fuel.E10, item, location["E10"], False)
            apply_yes_no(Fuel.OCTANE_91, item, location["ULP"], False)
            apply_yes_no(Fuel.OCTANE_95, item, location["VX95"] or location["PULP"], False)
            apply_yes_no(Fuel.OCTANE_98, item, location["VX98"] or location["SPULP"], False)
            apply_yes_no(Fuel.LPG, item, location["LPG"], False)
            apply_yes_no(Fuel.DIESEL, item, location["DSL"] or location["VXDSL"] or location["ATDSL"], False)
            apply_yes_no(Fuel.ADBLUE, item, location["ADBLU"], False)
            apply_yes_no(Fuel.PROPANE, item, location["BBQGas"], False)
            
            yield item
