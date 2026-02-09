import json

from scrapy import Spider

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class ZEnergyNZSpider(Spider):
    name = "z_energy_nz"
    start_urls = ["https://www.z.co.nz/find-a-station", "https://www.caltex.co.nz/find-a-station"]
    BRANDS = {
        "z": {"brand": "Z", "brand_wikidata": "Q8063337"},
        "caltex": {"brand": "Caltex", "brand_wikidata": "Q277470"},
    }

    def parse(self, response, **kwargs):
        for location in json.loads(
            response.xpath('//script[contains(text(), "stations")]/text()').re_first(r"({\"stations\":.+});")
        )["stations"]:
            item = DictParser.parse(location)

            if brand := self.BRANDS.get(response.url.split(".")[1]):
                item.update(brand)
                item["branch"] = item.pop("name").removeprefix("Z ").removeprefix("Caltex ")
            else:
                self.logger.error("Unknown brand: {}".format(response.url))

            item["ref"] = location["site_id"]
            item["website"] = response.urljoin(location["link"])
            item["opening_hours"] = self.parse_opening_hours(location["opening_hours"])

            if location["type_slug"] == "airstop":
                apply_category({"aeroway": "fuel"}, item)
            elif location["type_slug"] == "service-station":
                apply_category(Categories.FUEL_STATION, item)
            elif location["type_slug"] == "truck-stop":
                apply_category(Categories.FUEL_STATION, item)
                apply_yes_no("hgv=only", item, True)

            apply_yes_no(Fuel.DIESEL, item, any("Diesel" in s["name"] for s in location["fuels"]))
            apply_yes_no(
                Fuel.OCTANE_91,
                item,
                any("Z91" in s["name"] for s in location["fuels"])
                or any("Regular" in s["name"] for s in location["fuels"]),
            )
            apply_yes_no(Fuel.OCTANE_95, item, any("Premium" in s["name"] for s in location["fuels"]))
            apply_yes_no(Fuel.ADBLUE, item, any("AdBlue" in s["name"] for s in location["services"]))
            apply_yes_no(Fuel.ELECTRIC, item, any("evcharging" == s["code"] for s in location["services"]))
            apply_yes_no(Fuel.LPG, item, any("LPG" in s["name"] for s in location["services"]))

            apply_yes_no(Extras.TOILETS, item, any("Bathrooms" in s["name"] for s in location["services"]))
            apply_yes_no(Extras.CAR_WASH, item, any("wash" in s["name"] for s in location["services"]))
            apply_yes_no(Extras.ATM, item, any("ATM" in s["name"] for s in location["services"]))

            if postcode := item.get("postcode"):
                item["postcode"] = str(postcode)

            yield item

    def parse_opening_hours(self, business_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in business_hours:
            if rule["hours"] == "Open 24 hours":
                oh.add_range(rule["day"], "00:00", "24:00")
            else:
                # slightly hacky approach
                hours_string = f"{rule['day']}: {rule['hours']}"
                oh.add_ranges_from_string(hours_string)
        return oh
