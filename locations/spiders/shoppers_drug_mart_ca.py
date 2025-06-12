from typing import Any, Iterable

from scrapy import Request, Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.geo import city_locations
from locations.hours import DAYS_EN, DAYS_FR, OpeningHours, sanitise_day

BRANDS = {
    "PHARMAPRIX": ({"brand": "Pharmaprix", "brand_wikidata": "Q1820137"}, Categories.PHARMACY),
    "Pharmaprix Simplement Santé": None,
    "SHOPPERS DRUG MART": ({"brand": "Shoppers Drug Mart", "brand_wikidata": "Q1820137"}, Categories.PHARMACY),
    "SHOPPERS SIMPLY PHARMACY": ({"brand": "Shoppers Drug Mart", "brand_wikidata": "Q1820137"}, Categories.PHARMACY),
    "SPECIALTY HEALTH NETWORK": None,
}


class ShoppersDrugMartCASpider(Spider):
    name = "shoppers_drug_mart_ca"

    def start_requests(self) -> Iterable[Request]:
        for store_type in ["pharmaprix", "shoppersdrugmart"]:
            for city in city_locations("CA", 90000):
                yield JsonRequest(
                    url=f"https://api.shoppersdrugmart.ca/beauty/v2/{store_type}/store-locator/search?lang=en",
                    headers={"x-apikey": "r3kEMAxRsQQtyjXiIJOTFNN75vcsJFxH"},
                    data={"radius": 5000.166034400522, "longitude": city["longitude"], "latitude": city["latitude"]},
                )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["layout"]["sections"]["mainContentCollection"]["components"][0]["data"]:
            item = DictParser.parse(store)
            item["ref"] = item["website"] = store["viewStoreDetailsCTA"]

            item["opening_hours"] = self.parse_opening_hours(store["storeHours"])

            if props := BRANDS.get(store["bannerName"]):
                item.update(props[0])
                apply_category(props[1], item)

                yield item

    def parse_opening_hours(self, rules: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in rules:
            day = sanitise_day(rule["nameOfDay"], DAYS_FR | DAYS_EN)
            if rule["timeRange"] == "Closed":
                oh.set_closed(day)
            elif rule["timeRange"] == "24 hours":
                oh.add_range(day, "00:00", "24:00")
            else:
                oh.add_range(
                    day, *rule["timeRange"].replace("Midnight", "12:00 AM").split(" - "), time_format="%I:%M %p"
                )

        return oh
