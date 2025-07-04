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
            item["ref"] = store.get("UID")
            item["housenumber"] = store.get("House number")
            item["name"] = store.get("Additional Company Info")
            item["phone"] = "; ".join(
                filter(
                    None,
                    [
                        store.get("Telephone No."),
                        store.get("N° Portable"),
                    ],
                )
            )
            if "XPRESS" in item["name"].upper():
                item.update(self.AVIA_XPRESS)
            apply_category(Categories.FUEL_STATION, item)

            self.apply_attribute(Fuel.ADBLUE, item, [store.get("Ad blue pomp"), store.get("adblue")])
            self.apply_attribute(Fuel.E10, item, store.get("SP95/10"))
            self.apply_attribute(Fuel.E5, item, [store.get("SP95/E5"), store.get("SP98/E5")])
            self.apply_attribute(Fuel.DIESEL, item, [store.get("diesel b7"), store.get("Diesel B10")])
            self.apply_attribute(Fuel.E85, item, store.get("e85"))
            self.apply_attribute(Fuel.BIODIESEL, item, store.get("HVO"))
            self.apply_attribute(Fuel.CNG, item, store.get("CNG/GNC"))
            self.apply_attribute(Fuel.LNG, item, store.get("LNG/GNL"))
            self.apply_attribute(Fuel.LPG, item, store.get("LPG/GPL"))
            self.apply_attribute(Fuel.LH2, item, store.get("H2"))

            self.apply_attribute(FuelCards.AVIA, item, store.get("AVIA-CARD F"))
            self.apply_attribute(FuelCards.DKV, item, store.get("DKV"))
            self.apply_attribute(FuelCards.UTA, item, store.get("UTA"))
            self.apply_attribute(FuelCards.EUROWAG, item, store.get("EUROWAG"))
            self.apply_attribute(FuelCards.ROUTEX, item, store.get("ROUTEX"))
            self.apply_attribute(FuelCards.MORGAN_FUELS, item, store.get("MORGAN FUELS"))
            self.apply_attribute(FuelCards.E100, item, store.get("E100"))
            self.apply_attribute(FuelCards.ESSO_NATIONAL, item, store.get("ESSO"))
            self.apply_attribute(FuelCards.SHELL, item, [store.get("Shell M Card"), store.get("Shell S Card")])

            self.apply_attribute(PaymentMethods.AMERICAN_EXPRESS, item, store.get("AMEX"))
            self.apply_attribute(PaymentMethods.MASTER_CARD, item, store.get("MASTERCARD"))
            self.apply_attribute(PaymentMethods.VISA, item, store.get("VISA"))

            self.apply_attribute(Access.HGV, item, store.get("truck_station"))
            self.apply_attribute(
                Extras.CAR_WASH, item, [store.get("gantry car wash"), store.get("Jetwash"), store.get("car wash")]
            )
            self.apply_attribute(Extras.WIFI, item, store.get("wifi"))

            yield item

    def apply_attribute(self, attribute: str | Enum, item: Feature, value: str | list[str]) -> None:
        if not isinstance(value, list):
            value = [value]
        apply_yes_no(attribute, item, any(v == "TRUE" for v in value))
