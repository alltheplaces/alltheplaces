from typing import Iterable

from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider


class TangoSpider(JSONBlobSpider):
    name = "tango"
    item_attributes = {"brand": "Tango", "brand_wikidata": "Q125867683"}
    locations_key = "results"

    async def start(self) -> Iterable[JsonRequest]:
        yield JsonRequest(
            url="https://www.tango.nl/api/poi/locations",
            data={
                "query": {
                    "hasFueling": True,
                    "locationTypes": ["Tango"],
                    "serviceCodes": [],
                    "latitude": 52.1326,
                    "longitude": 5.2913,
                    "radius": 500000,
                    "take": 1000,
                }
            },
        )

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["street_address"] = item.pop("street")
        item["website"] = f'https://www.tango.nl/stations/{item["name"].lower().replace(" ", "-")}'
        item["branch"] = item.pop("name").removeprefix("Tango ")
        item["phone"] = feature["q8Los"].get("phoneNumber")
        item["opening_hours"] = self.parse_opening_hours(feature["q8Los"].get("shopOpeningHours"))

        fuel_data = (feature.get("fuelingLos") or {}).get("fuels") or []
        services = feature["q8Los"].get("facilities") or []
        fuels = [fuel["code"].removeprefix("$FP$") for fuel in fuel_data]
        services = [service["code"].removeprefix("$SF$") for service in services]

        apply_yes_no(Extras.CAR_WASH, item, "CARWASH" in services)

        apply_yes_no(Fuel.ADBLUE, item, "ADBLUE" in fuels)
        apply_yes_no(Fuel.DIESEL, item, "DIESEL" in fuels)
        apply_yes_no(Fuel.LPG, item, "LPG" in fuels)
        apply_yes_no(Fuel.E10, item, "PETROL_EURO_95" in fuels)
        apply_yes_no(Fuel.E5, item, "PETROL_SUPERPLUS_98" in fuels)

        apply_category(Categories.FUEL_STATION, item)
        yield item

    def parse_opening_hours(self, opening_hours: list) -> OpeningHours:
        oh = OpeningHours()
        for rule in opening_hours:
            open_time = str(rule["startHour"]).zfill(2) + ":" + str(rule["startMinute"]).zfill(2)
            close_time = str(rule["endHour"]).zfill(2) + ":" + str(rule["endMinute"]).zfill(2)
            oh.add_range(rule["dayCode"], open_time, close_time)
        return oh
