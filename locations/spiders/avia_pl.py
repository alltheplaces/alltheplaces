import re
from typing import Any

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, FuelCards, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.avia_de import AVIA_SHARED_ATTRIBUTES

FUELS_AND_SERVICES_MAPPING = {
    # Fuels
    "adblue": Fuel.ADBLUE,
    "diesel": Fuel.DIESEL,
    "diesel_gold": Fuel.DIESEL,
    "gas_98": Fuel.OCTANE_98,
    "gas_95": Fuel.OCTANE_95,
    "lpg": Fuel.LPG,
    "hvo": Fuel.BIODIESEL,
    # Fuel cards
    "eurowag": FuelCards.EUROWAG,
    "dkv": FuelCards.DKV,
    "uta": FuelCards.UTA,
    "avia": FuelCards.AVIA,
    "e100": FuelCards.E100,
}


class AviaPLSpider(Spider):
    name = "avia_pl"
    item_attributes = AVIA_SHARED_ATTRIBUTES
    start_urls = ["https://b2c.aviastacjapaliw.pl/static/js/main.bd46d667.js"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        token = re.search(r"Authorization:\"Bearer.*concat\(\"(.*)\"\)}}\)", response.text).group(1)
        yield scrapy.Request(
            url="https://mapa.aviastacjapaliw.pl/api/stations?populate[0]=logo&populate[1]=address&populate[2]=coordinates&populate[3]=opening_hours&populate[4]=features.stations&populate[5]=features.fuels&populate[6]=features.cards&populate[7]=features.services&populate[8]=station_types&filters[station_types][type][$eq]=B2C",
            headers={"Authorization": "Bearer " + token},
            callback=self.parse_locations,
        )

    #
    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for station in response.json()["data"]:
            item = DictParser.parse(station)
            item["branch"] = item.pop("name")
            apply_category(Categories.FUEL_STATION, item)
            for key in ["cards", "fuels"]:
                for tag, value in station["features"][key].items():
                    if not isinstance(value, bool):
                        continue
                    apply_yes_no(FUELS_AND_SERVICES_MAPPING[tag], item, True if value else False)
            yield item
