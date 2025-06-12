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
            item["street"] = store["bannerName"]
            item["opening_hours"] = OpeningHours()
            for day_time in store["storeHours"]:
                day = day_time["nameOfDay"]
                times = day_time["timeRange"]
                if times == "Closed":
                    continue
                elif times == "24 hours":
                    times = "12:00 AM - 12:00 AM"
                times = times.replace("Midnight", "12:00 AM")

                item["opening_hours"].add_range(
                    sanitise_day(day, DAYS_FR | DAYS_EN), *times.split(" - "), time_format="%I:%M %p"
                )

            if props := BRANDS.get(store["bannerName"]):
                item.update(props[0])
                apply_category(props[1], item)

            yield item
