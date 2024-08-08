from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours
from locations.spiders.q8_italia import Q8ItaliaSpider


class F24Spider(Spider):
    name = "f24"
    start_urls = [
        "https://www.f24.dk/-/Station/GetGlobalMapStations?appDataSource=6d56d51e-5ab9-4caf-a18f-20c07ec0fba5"
    ]

    BRANDS = {
        "F24": {"brand": "F24", "brand_wikidata": "Q12310853"},
        "Q8": Q8ItaliaSpider.item_attributes,
    }

    def parse(self, response, **kwargs):
        for location in response.json()["stations"]:
            location["ref"] = str(location["stationNumber"])
            location["geo"] = location.pop("position")
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)

            item["website"] = f'https://www.f24.dk{location["url"]}'

            if location.get("openingHours"):
                if location["openingHours"]["AlwaysOpen"]:
                    item["opening_hours"] = "24/7"
                else:
                    item["opening_hours"] = OpeningHours()
                    for rule in ["WeekDays", "Saturday", "Sunday"]:
                        self.add_rule(item["opening_hours"], rule, location["openingHours"].get(rule))

            if brand := self.BRANDS.get(location["net"]):
                item.update(brand)

            apply_category(Categories.FUEL_STATION, item)

            yield item

    @staticmethod
    def add_rule(oh: OpeningHours, day: str, rule: dict):
        if rule.get("Closed"):
            return
        if day == "WeekDays":
            oh.add_days_range(DAYS[:5], rule["From"], rule["To"])
        else:
            oh.add_range(day, rule["From"], rule["To"])
