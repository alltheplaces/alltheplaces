import re
from typing import Any

import scrapy
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Fuel, FuelCards, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
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
    start_urls = ["https://b2c.aviastacjapaliw.pl/"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield from response.follow_all(
            response.xpath('//script[contains(@src, "main")]/@src').getall(), self.parse_token
        )

    def parse_token(self, response: Response, **kwargs: Any) -> Any:
        token = re.search(r"Authorization:\"Bearer.*concat\(\"(.*)\"\)}}\)", response.text).group(1)
        yield scrapy.Request(
            url="https://mapa.aviastacjapaliw.pl/api/stations?populate[0]=logo&populate[1]=address&populate[2]=coordinates&populate[3]=opening_hours&populate[4]=features.stations&populate[5]=features.fuels&populate[6]=features.cards&populate[7]=features.services&populate[8]=station_types&filters[station_types][type][$eq]=B2C",
            headers={"Authorization": "Bearer " + token},
            callback=self.parse_locations,
        )

    def parse_locations(self, response: Response, **kwargs: Any) -> Any:
        for station in response.json()["data"]:
            item = DictParser.parse(station)
            item["branch"] = item.pop("name").removeprefix("AVIA ")
            item["website"] = "https://aviastacjapaliw.pl/mapa-stacji?target_station={}".format(
                station["name"].lower().replace(" ", "+")
            )

            try:
                item["opening_hours"] = self.parse_opening_hours(station["opening_hours"])
            except:
                self.logger.error("Error parsing opening hours")

            apply_category(Categories.FUEL_STATION, item)

            for key in ["cards", "fuels"]:
                for tag, value in station["features"][key].items():
                    if not isinstance(value, bool):
                        continue
                    if fuel_and_services := FUELS_AND_SERVICES_MAPPING.get(tag):
                        apply_yes_no(fuel_and_services, item, True if value else False)

            yield item

    def parse_opening_hours(self, opening_hours: dict) -> OpeningHours | str:
        if opening_hours["is_24h"] is True:
            return "24/7"

        oh = OpeningHours()
        oh.add_days_range(
            ["Mo", "Tu", "We", "Th", "Fr"],
            opening_hours["working_days_start"],
            opening_hours["working_days_end"],
            "%H:%M:%S.%f",
        )
        oh.add_range("Sa", opening_hours["saturday_start"], opening_hours["saturday_end"], "%H:%M:%S.%f")
        oh.add_range("Su", opening_hours["sunday_start"], opening_hours["sunday_end"], "%H:%M:%S.%f")

        return oh
