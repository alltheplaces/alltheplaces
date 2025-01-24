from scrapy import Request, Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS_GR, OpeningHours, day_range


class AlphaBankGRSpider(Spider):
    name = "alpha_bank_gr"
    item_attributes = {"brand": "Alpha Bank", "brand_wikidata": "Q747394"}

    def start_requests(self):
        yield Request(url="https://www.alpha.gr/api/maps/MapLocations?bringPrivates=False&httproute=True")

    def parse(self, response):
        data = response.json()
        for branch in data.get("Branches", []):
            item = self.parse_poi(branch)
            apply_category(Categories.BANK, item)
            item["branch"] = item.pop("name")

            yield item

        for atm in data.get("Atms", []):
            item = self.parse_poi(atm)
            apply_category(Categories.ATM, item)
            item["branch"] = item.pop("name")

            yield item

    def parse_poi(self, poi):
        item = DictParser.parse(poi)
        item["street_address"] = poi.get("AddressMain")
        item["city"] = poi.get("Cityname")
        if poi.get("AccesWeeklyDesc", "") == "Όλο το 24ωρο":
            item["opening_hours"] = "Mo-Su 00:00-24:00"
        elif poi.get("hours") or poi.get("AccesWeeklyDesc"):
            if poi.get("hours"):
                hours = poi.get("hours").lower()
            elif poi.get("AccesWeeklyDesc"):
                hours = poi.get("AccesWeeklyDesc").lower()

            try:
                # Most are like "Monday - Friday 08:00 - 14:30" if not 24 hours
                hours = hours.replace(" - ", "-").split(" ")
                oh = OpeningHours()
                days = day_range(DAYS_GR[hours[0].capitalize()], DAYS_GR[hours[2].capitalize()])
                oh.add_days_range(days, hours[3].split("-")[0], hours[3].split("-")[1])
                item["opening_hours"] = oh.as_opening_hours()
            except Exception:
                pass

        return item
