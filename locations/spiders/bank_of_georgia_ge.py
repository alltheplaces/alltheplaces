from typing import Any

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.items import Feature

# ATM-type objectType -> Categories enum. "SC" (branches) and "PBX" (self-service
# payment terminals) are handled explicitly in parse.
ATM_CATEGORIES = {
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
            item["street_address"] = location["addressGe"]
            item["city"] = location["cityGe"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]
            if location.get("worksFullTime") == "Y":
                item["opening_hours"] = "24/7"

            if object_type == "PBX":  # self-service payment terminal; no Categories enum for this tag
                apply_category({"amenity": "payment_terminal"}, item)
            elif object_type == "SC":  # service-centre branch
                apply_category(Categories.BANK, item)
                # nameGe is the branch format (Standard/Express/...) except for "Solo", Bank of
                # Georgia's premium sub-brand: keep that as the name (NSI supplies the Bank of
                # Georgia name for every other branch), and drop the rest as non-names.
                if location.get("objectSubType") == "SOL":
                    item["name"] = location["nameGe"]
            elif category := ATM_CATEGORIES.get(object_type):
                apply_category(category, item)
                item["branch"] = location["nameGe"]  # host venue, e.g. "SuperMarket"
            else:
                self.logger.error("Unexpected objectType: {}".format(object_type))
                continue

            apply_yes_no(Extras.WHEELCHAIR, item, location.get("isAdapted") == "Y")
            for currency in location.get("atmCcys") or []:
                item["extras"]["currency:{}".format(currency)] = "yes"

            yield item
