from scrapy import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class OKQ8Spider(Spider):
    name = "okq8"
    start_urls = [
        "https://www.okq8.se/-/Station/GetGlobalMapStations?appDataSource=9d780912-2801-4457-9376-16c48d02e688"
    ]

    BRANDS = {
        "OKQ8": {"brand": "OKQ8", "brand_wikidata": "Q2789310"},
        "Tanka": {"brand": "Tanka", "brand_wikidata": "Q10690640"},
        "IDS": None,  # {"brand": "Ids"} # Some kind of private? HGV?
        "Eon": None,  # {"brand": "Eon"} # ?
    }

    def parse(self, response, **kwargs):
        for location in response.json()["stations"]:
            location["ref"] = str(location["stationNumber"])
            location["geo"] = location.pop("position")
            location["street_address"] = location.pop("address")
            item = DictParser.parse(location)

            # TODO: parse fuel types uisng response.json()["filters"]

            item["website"] = f'https://www.okq8.se{location["url"]}'

            if location.get("openingHours"):
                if location["openingHours"]["AlwaysOpen"]:
                    item["opening_hours"] = "24/7"
                else:
                    item["opening_hours"] = OpeningHours()
                    for rule in ["WeekDays", "Saturday", "Sunday"]:
                        self.add_rule(item["opening_hours"], rule, location["openingHours"].get(rule))

            apply_category(Categories.FUEL_STATION, item)

            if brand := self.BRANDS.get(location["net"]):
                item.update(brand)

                yield item  # Other brands too small to worry about right now

    @staticmethod
    def add_rule(oh: OpeningHours, day: str, rule: dict):
        if rule.get("Closed"):
            return
        if day == "WeekDays":
            oh.add_days_range(DAYS[:5], rule["From"], rule["To"])
        else:
            oh.add_range(day, rule["From"], rule["To"])
