from enum import Enum
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import (
    Access,
    Categories,
    Extras,
    Fuel,
    FuelCards,
    PaymentMethods,
    apply_category,
    apply_yes_no,
)
from locations.dict_parser import DictParser
from locations.items import Feature
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES
from locations.user_agents import BROWSER_DEFAULT


class AviaFRSpider(Spider):
    name = "avia_fr"
    item_attributes = AVIA_SHARED_ATTRIBUTES
    AVIA_XPRESS = {"brand": "Avia XPress", "brand_wikidata": "Q124611203"}
    user_agent = BROWSER_DEFAULT
    start_urls = ["https://www.avia-france.fr/wp-admin/admin-ajax.php?action=get_avia_csv"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json()["data"]:
            if any(store.get(key, "") == "TRUE" for key in ["Station temporarily closed", "Fuel agency"]):
                continue
            store["postcode"] = store.pop("ZIP Code")
            item = DictParser.parse(store)
            item["branch"] = item.pop("name")
            item["lat"] = store.get("geo lat")
            item["lon"] = store.get("geo long")
            if email := item.get("email"):
                item["email"] = email.split("/")[0].replace(" ", "")
            item["ref"] = store.get("UID")
            item["housenumber"] = store.get("House number")
            item["state"] = store.get("Place")
            item["phone"] = store.get("Phone No.")
            if express := store.get("XPRESS"):
                if express == "TRUE":
                    item.update(self.AVIA_XPRESS)
            apply_category(Categories.FUEL_STATION, item)

            self.apply_attribute(Fuel.ADBLUE, item, store.get("AdBlue pump"))
            self.apply_attribute(Fuel.E10, item, store.get("SP95/10"))
            self.apply_attribute(Fuel.E5, item, [store.get("SP95/E5"), store.get("SP98/E5")])
            self.apply_attribute(Fuel.DIESEL, item, [store.get("Diesel B7"), store.get("Diesel B10")])
            self.apply_attribute(Fuel.E85, item, store.get("E85"))
            self.apply_attribute(Fuel.CNG, item, store.get("CNG"))
            self.apply_attribute(Fuel.LNG, item, store.get("LNG"))
            self.apply_attribute(Fuel.LPG, item, store.get("LPG"))
            self.apply_attribute(Fuel.LH2, item, store.get("H2"))

            self.apply_attribute(FuelCards.DKV, item, store.get("DKV"))
            self.apply_attribute(FuelCards.UTA, item, store.get("UTA"))
            self.apply_attribute(FuelCards.EUROWAG, item, store.get("EUROWAG"))
            self.apply_attribute(FuelCards.ROUTEX, item, store.get("ROUTEX"))
            self.apply_attribute(FuelCards.MORGAN_FUELS, item, store.get("MORGAN FUELS"))
            self.apply_attribute(FuelCards.E100, item, store.get("E100"))
            self.apply_attribute(FuelCards.ESSO_NATIONAL, item, store.get("ESSO"))
            self.apply_attribute(FuelCards.SHELL, item, [store.get("Shell M"), store.get("Shell S")])

            self.apply_attribute(PaymentMethods.AMERICAN_EXPRESS, item, store.get("AMEX"))
            self.apply_attribute(PaymentMethods.MASTER_CARD, item, store.get("MASTERCARD"))
            self.apply_attribute(PaymentMethods.VISA, item, store.get("VISA"))

            self.apply_attribute(Access.HGV, item, store.get("Truck station"))
            self.apply_attribute(Extras.CAR_WASH, item, [store.get("Gantry wash"), store.get("Jetwash")])
            self.apply_attribute(Extras.WIFI, item, store.get("wifi"))

            yield item

    def apply_attribute(self, attribute: str | Enum, item: Feature, value: str | list[str]) -> None:
        if not isinstance(value, list):
            value = [value]
        apply_yes_no(attribute, item, any(v == "TRUE" for v in value))
