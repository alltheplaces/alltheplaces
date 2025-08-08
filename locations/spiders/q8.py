from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.q8_italia import Q8ItaliaSpider


# AKA Q8 NWE https://www.q8.be/nl/stations
class Q8Spider(JSONBlobSpider):
    name = "q8"
    start_urls = ["https://www.q8.be/fr/get/stations.json"]

    BRANDS = {
        "Q8Easy": {"brand": "Q8 Easy", "brand_wikidata": "Q1806948"},
        "Q8": Q8ItaliaSpider.item_attributes,
    }
    locations_key = "results"

    def start_requests(self) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://www.q8.be/api/poi/locations",
            data={
                "query": {
                    "latitude": 50.46192477912935,
                    "longitude": 4.469899999999987,
                    "radius": 600000,
                    "take": 2000,
                    "hasFueling": True,
                    "locationTypes": ["Q8", "Q8Easy"],
                    "serviceCodes": [],
                }
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street")
        item["branch"] = item.pop("name").title().removeprefix("Q8 ").removeprefix("Easy ")
        item["phone"] = feature["q8Los"].get("phoneNumber")

        if brand := self.BRANDS.get(feature["q8Los"]["locationType"]):
            item.update(brand)
        apply_category(Categories.FUEL_STATION, item)

        item["opening_hours"] = self.parse_opening_hours(feature["q8Los"].get("shopOpeningHours"))

        fuel_data = (feature.get("fuelingLos") or {}).get("fuels") or []
        fuels = [fuel["code"].removeprefix("$FP$") for fuel in fuel_data]
        apply_yes_no(Fuel.ADBLUE, item, "ADBLUE" in fuels)
        apply_yes_no(Fuel.CNG, item, "CNG" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "DIESEL" in fuels)
        apply_yes_no(Fuel.LPG, item, "LPG" in fuels)
        apply_yes_no(Fuel.E10, item, "PETROL_EURO_95" in fuels)
        apply_yes_no(Fuel.E5, item, "PETROL_SUPERPLUS_98" in fuels)

        yield item

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            open_time = str(rule["startHour"]).zfill(2) + ":" + str(rule["startMinute"]).zfill(2)
            close_time = str(rule["endHour"]).zfill(2) + ":" + str(rule["endMinute"]).zfill(2)
            oh.add_range(rule["dayCode"], open_time, close_time)
        return oh
