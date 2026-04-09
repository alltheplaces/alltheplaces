from typing import Any, AsyncIterator
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range

CATEGORIES_MAPPING = {
    # Octane 95
    "finland/95extra": Fuel.OCTANE_95,
    "norway/95bensin": Fuel.OCTANE_95,
    "sweden/95blyfri": Fuel.OCTANE_95,
    # Octane 98
    "finland/98": Fuel.OCTANE_98,
    "norway/98bensin": Fuel.OCTANE_98,
    "sweden/98blyfri": Fuel.OCTANE_98,
    # Formulas
    "sweden/e85": Fuel.E85,
    # Diesel
    "finland/diesel20": Fuel.DIESEL,
    "finland/diesel35": Fuel.DIESEL,
    "finland/diesel38": Fuel.DIESEL,
    "finland/dieselHVO": [Fuel.DIESEL, Fuel.BIODIESEL],
    "finland/twoqualitydiesel": Fuel.DIESEL,
    "norway/diesel": Fuel.DIESEL,
    "sweden/diesel": Fuel.DIESEL,
    # Biodiesel
    "finland/mpohvo": Fuel.BIODIESEL,
    "norway/hvo100": Fuel.BIODIESEL,
    "sweden/hvo": Fuel.BIODIESEL,
    # AdBlue
    "finland/adblue": Fuel.ADBLUE,
    "finland/adblueprivatecars": Fuel.ADBLUE,
    "norway/truckadblue": Fuel.ADBLUE,
    "sweden/adblue": Fuel.ADBLUE,
    "sweden/adbluepump": Fuel.ADBLUE,
    # Electric
    "sweden/elbilsladdning150": Fuel.ELECTRIC,
    "sweden/elbilsladdning400": Fuel.ELECTRIC,
    "finland/evCharging": Fuel.ELECTRIC,
    "norway/evcharging": Fuel.ELECTRIC,
    "norway/elcharging": Fuel.ELECTRIC,
    "sweden/laddstation": Fuel.ELECTRIC,
    "norway/truckevcharging": Fuel.ELECTRIC,
    # HGV
    "finland/truckfuelingpoint": Access.HGV,
    "finland/trucklengthunder14": Access.HGV,
    "finland/trucklengthunder2525": Access.HGV,
    "finland/trucklengthunder345": Access.HGV,
    "norway/truckfacilities": Access.HGV,
    "norway/truckparking": Access.HGV,
    "sweden/truckstation": Access.HGV,
    "sweden/trucklengthunder14": Access.HGV,
    "sweden/trucklengthunder255": Access.HGV,
    "norway/truckdiesel": Fuel.HGV_DIESEL,
    # Car Wash
    "finland/selfservicecarwash": Extras.CAR_WASH,
    "finland/perfectcarwash": Extras.CAR_WASH,
    "finland/perfectcarwash24hours": Extras.CAR_WASH,
    "finland/othercarwash": Extras.CAR_WASH,
    "norway/carwash": Extras.CAR_WASH,
    "norway/norwegianshellcarwash": Extras.CAR_WASH,
    "sweden/carwash": Extras.CAR_WASH,
    "sweden/dirtcarwash": Extras.CAR_WASH,
    "sweden/selfservicecarwash": Extras.CAR_WASH,
    # Food
    "finland/helmisimpukka": "food",
    "finland/helmisimpukkarestaurant": "food",
    "finland/breakfastbuffet": "food",
    "finland/lunch": "food",
    "finland/weekendlunch": "food",
    "finland/burgerking": "food",
    "finland/kotipizza": "food",
    "finland/pizza": "food",
    "norway/realfood": "food",
    "sweden/food": "food",
    "sweden/fastfood": "food",
    # Misc
    "norway/defibrillator": "emergency:defibrillator",
    "norway/coloredagoonpump": Fuel.UNTAXED_DIESEL,
    "finland/atm": Extras.ATM,
}


class St1Spider(Spider):
    name = "st1"
    allowed_domains = ["st1.fi", "st1.no", "st1.se"]
    ST1 = {"brand": "St1", "brand_wikidata": "Q7592214"}
    HELMISIMPUKKA = {"brand": "HelmiSimpukka"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        configs = [
            {
                "url": "https://st1.fi/proxy/cms-view/v1/content/page?path=asemahaku",
                "headers": {"x-st1-locale": "fi-FI"},
                "base_url": "https://st1.fi/",
            },
            {
                "url": "https://st1.no/proxy/cms-view/v1/content/page?path=finn-stasjon",
                "headers": {"x-st1-locale": "no-NO"},
                "base_url": "https://st1.no/",
            },
            {
                "url": "https://st1.se/proxy/cms-view/v1/content/page?path=hitta-station",
                "headers": {"x-st1-locale": "sv-SE"},
                "base_url": "https://st1.se/",
            },
        ]

        for cfg in configs:
            yield JsonRequest(
                url=cfg["url"],
                headers=cfg["headers"],
                meta={"base_url": cfg["base_url"]},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        data = response.json()
        base_url = response.meta.get("base_url", "")

        content = data.get("content") or {}
        for body in content.get("body") or []:
            # Ignore other CMS entries
            if body.get("type") != "stationlocator":
                continue

            for entry in body.get("data") or []:
                station = entry.get("station") or {}
                if not station:
                    continue

                # Only collect St1-branded sites
                if station.get("brand") != "St1":
                    continue

                # Parse basic fields
                item = DictParser.parse(station)
                item["street_address"] = item.pop("street")

                if item["name"].startswith("HelmiSimpukka Express"):
                    item.update(self.HELMISIMPUKKA)
                    apply_category(Categories.FAST_FOOD, item)
                    item["branch"] = item.pop("name").removeprefix("HelmiSimpukka Express")
                    item["name"] = "HelmiSimpukka Express"
                elif item["name"].strip().startswith("St1 ") or item["name"].startswith("ST1 "):
                    item.update(self.ST1)
                    apply_category(Categories.FUEL_STATION, item)
                    item["branch"] = item.pop("name").removeprefix("St1 ").removeprefix("ST1 ")

                # Website
                if path := entry.get("path"):
                    item["website"] = urljoin(base_url, path)

                # Opening hours
                opening_hours_table = (station.get("openingHoursTable") or {}).get("station") or []
                if opening_hours_table:
                    oh = OpeningHours()

                    for rule in opening_hours_table:
                        hours = rule.get("hours") or []
                        for period in hours:
                            start_time = period.get("startTime")
                            end_time = period.get("endTime")
                            if not start_time or not end_time:
                                continue

                            for day in day_range(rule.get("from"), rule.get("to")):
                                oh.add_range(day, start_time, end_time)

                    item["opening_hours"] = oh.as_opening_hours()

                # Additional attributes from categories mapping
                self.parse_attribute(item, station.get("fuels") or [], CATEGORIES_MAPPING)
                self.parse_attribute(item, station.get("chargings") or [], CATEGORIES_MAPPING)
                self.parse_attribute(item, station.get("services") or [], CATEGORIES_MAPPING)
                self.parse_attribute(item, station.get("trucks") or [], CATEGORIES_MAPPING)

                yield item

    def parse_attribute(self, item, values: list, mapping: dict):
        for value in values:
            if tags := mapping.get(value):
                if isinstance(tags, (list, tuple)):
                    for tag in tags:
                        apply_yes_no(tag, item, True)
                else:
                    apply_yes_no(tags, item, True)
