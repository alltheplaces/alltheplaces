from itertools import chain
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
    "finland/dieselHVO": (Fuel.DIESEL, Fuel.BIODIESEL),
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

ATTRIBUTE_KEYS = ("fuels", "chargings", "services", "trucks")

SITES = (
    ("https://st1.fi/", "asemahaku", "fi-FI"),
    ("https://st1.no/", "finn-stasjon", "no-NO"),
    ("https://st1.se/", "hitta-station", "sv-SE"),
)


class St1Spider(Spider):
    name = "st1"
    allowed_domains = ["st1.fi", "st1.no", "st1.se"]
    ST1 = {"brand": "St1", "brand_wikidata": "Q7592214"}
    HELMISIMPUKKA = {"brand": "HelmiSimpukka"}
    requires_proxy = True

    async def start(self) -> AsyncIterator[JsonRequest]:
        for base_url, path, locale in SITES:
            yield JsonRequest(
                url=urljoin(base_url, f"proxy/cms-view/v1/content/page?path={path}"),
                headers={"x-st1-locale": locale},
                meta={"base_url": base_url},
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        base_url = response.meta["base_url"]
        bodies = (response.json().get("content") or {}).get("body") or []

        for body in bodies:
            if body.get("type") != "stationlocator":
                continue

            for entry in body.get("data") or []:
                station = entry.get("station") or {}
                # Only collect St1-branded sites
                if station.get("brand") != "St1":
                    continue

                item = DictParser.parse(station)
                item["street_address"] = item.pop("street")

                name = item.pop("name")
                if name.startswith("HelmiSimpukka Express"):
                    item.update(self.HELMISIMPUKKA)
                    item["name"] = "HelmiSimpukka Express"
                    item["branch"] = name.removeprefix("HelmiSimpukka Express").strip()
                    apply_category(Categories.FAST_FOOD, item)
                elif (stripped := name.strip()).startswith(("St1 ", "ST1 ")):
                    item.update(self.ST1)
                    item["branch"] = stripped[4:]
                    apply_category(Categories.FUEL_STATION, item)
                else:
                    item["name"] = name

                if entry_path := entry.get("path"):
                    item["website"] = urljoin(base_url, entry_path)

                item["opening_hours"] = self.parse_opening_hours(station)

                for value in chain.from_iterable(station.get(key) or [] for key in ATTRIBUTE_KEYS):
                    tags = CATEGORIES_MAPPING.get(value)
                    if not tags:
                        continue
                    for tag in tags if isinstance(tags, (list, tuple)) else (tags,):
                        apply_yes_no(tag, item, True)

                yield item

    @staticmethod
    def parse_opening_hours(station: dict) -> OpeningHours | None:
        rules = (station.get("openingHoursTable") or {}).get("station") or []
        if not rules:
            return None

        oh = OpeningHours()
        for rule in rules:
            for period in rule.get("hours") or []:
                if not (start_time := period.get("startTime")) or not (end_time := period.get("endTime")):
                    continue
                for day in day_range(rule.get("from"), rule.get("to")):
                    oh.add_range(day, start_time, end_time, "%H:%M:%S")
        return oh
