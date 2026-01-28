import json

import scrapy

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ZEnergyNZSpider(scrapy.Spider):
    name = "z_energy_nz"
    item_attributes = {"brand": "Z", "brand_wikidata": "Q8063337"}
    start_urls = ["https://www.z.co.nz/find-a-station"]

    def parse(self, response, **kwargs):
        for location in json.loads(
            response.xpath('//script[contains(text(), "stations")]/text()').re_first(r"({\"stations\":.+});")
        )["stations"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("Z ")
            item["ref"] = location["site_id"]
            item["website"] = response.urljoin(location["link"])
            item["opening_hours"] = self.parse_opening_hours(location["opening_hours"])

            if location["type_slug"] == "airstop":
                apply_category({"aeroway": "fuel"}, item)
            elif location["type_slug"] == "service-station":
                apply_category(Categories.FUEL_STATION, item)
            elif location["type_slug"] == "truck-stop":
                apply_category(Categories.FUEL_STATION.value | {"hgv": "only"}, item)

            apply_yes_no(Fuel.DIESEL, item, any("Diesel" in s["name"] for s in location["fuels"]))
            apply_yes_no(Fuel.OCTANE_91, item, any("Z91" in s["name"] for s in location["fuels"]))
            apply_yes_no(Fuel.OCTANE_95, item, any("ZX Premium" in s["name"] for s in location["fuels"]))
            apply_yes_no(Fuel.ADBLUE, item, any("AdBlue" in s["name"] for s in location["services"]))
            apply_yes_no(Fuel.ELECTRIC, item, any("evcharging" == s["code"] for s in location["services"]))

            apply_yes_no(Fuel.ELECTRIC, item, any("evcharging" == s["code"] for s in location["services"]))

            if postcode := item.get("postcode"):
                item["postcode"] = str(postcode)

            yield item

    def parse_opening_hours(self, business_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in business_hours:
            if rule["hours"] == "Open 24 hours":
                oh.add_range(rule["day"], "00:00", "24:00")
            else:
                if " - " not in rule["hours"]:
                    # fixes for silly edge cases with Z Cashmere and Z Levin respectively
                    rule["hours"] = rule["hours"].replace(" -", " - ").replace("–", "-")
                times = rule["hours"].split(" - ")
                print(times)
                try:
                    oh.add_range(rule["day"], times[0], times[1], "%I:%M%p")
                except ValueError:
                    oh.add_range(rule["day"], times[0], times[1], "%I%p")
        return oh
