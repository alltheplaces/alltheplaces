from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature

# objectType -> Categories enum. "PBX" (self-service payment terminals) are handled
# separately as amenity=payment_terminal, which has no Categories enum yet.
CATEGORIES = {
    "SC": Categories.BANK,  # service centre / branch (objectSubType BOG/EXP/SOL/EPS)
    "ATM": Categories.ATM,
    "ATM_EUR": Categories.ATM,  # ATM that also dispenses EUR
    "CASHDEPS": Categories.ATM,  # cash-deposit machine
}


class BankOfGeorgiaGESpider(Spider):
    name = "bank_of_georgia_ge"
    item_attributes = {"brand": "საქართველოს ბანკი", "brand_wikidata": "Q2469733"}

    async def start(self) -> Any:
        yield JsonRequest(url="https://bankofgeorgia.ge/api/locations/searchLocations", data={})

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            object_type = location["objectType"]
            # Built manually rather than via DictParser: the source pairs every field
            # as *Ge/*En and we deliberately keep the Georgian values.
            item = Feature()
            item["ref"] = location["objectKey"]
            item["branch"] = location["nameGe"]
            item["street_address"] = location["addressGe"]
            item["city"] = location["cityGe"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            if location.get("worksFullTime") == "Y":
                item["opening_hours"] = "24/7"

            if object_type == "PBX":  # self-service payment terminal; no Categories enum for this tag
                apply_category({"amenity": "payment_terminal"}, item)
            elif category := CATEGORIES.get(object_type):
                apply_category(category, item)
            else:
                self.logger.error("Unexpected objectType: {}".format(object_type))
                continue

            apply_yes_no(Extras.WHEELCHAIR, item, location.get("isAdapted") == "Y")
            for currency in location.get("atmCcys") or []:
                item["extras"]["currency:{}".format(currency)] = "yes"

            yield item
