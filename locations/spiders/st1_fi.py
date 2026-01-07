from typing import AsyncIterator, Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range
from locations.items import Feature


class St1FISpider(Spider):
    name = "st1_fi"
    allowed_domains = ["st1.fi"]
    item_attributes = {
        "brand": "St1",
        "brand_wikidata": "Q7592214",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://st1.fi/proxy/cms-view/v1/content/page?path=asemahaku",
            headers={"x-st1-locale": "fi-FI"},
        )

    def parse(self, response) -> Iterable[Feature]:
        data = response.json()

        content = data.get("content")
        for body in content.get("body"):
            # Ignore other CMS entries
            if body.get("type") != "stationlocator":
                continue

            for entry in body.get("data"):
                station = entry.get("station")
                if not station:
                    continue

                # Only collect St1-branded sites
                if station.get("brand") != "St1":
                    continue

                # Parse basic fields
                item = DictParser.parse(station)

                # Website
                if path := entry.get("path"):
                    item["website"] = urljoin("https://st1.fi/", path)

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

                # Fuel types
                fuels = station.get("fuels") or []
                # Petrol
                apply_yes_no(Fuel.OCTANE_95, item, "finland/95extra" in fuels)
                apply_yes_no(Fuel.OCTANE_98, item, "finland/98" in fuels)
                # Diesel (any diesel variant counts as on-road diesel)
                apply_yes_no(
                    Fuel.DIESEL,
                    item,
                    any(
                        code in fuels
                        for code in [
                            "finland/diesel20",
                            "finland/diesel35",
                            "finland/diesel38",
                            "finland/dieselHVO",
                            "finland/twoqualitydiesel",
                        ]
                    ),
                )
                # Biodiesel / HVO
                apply_yes_no(
                    Fuel.BIODIESEL,
                    item,
                    any(code in fuels for code in ["finland/dieselHVO", "finland/mpohvo"]),
                )
                # AdBlue (generic AdBlue offer at the station)
                apply_yes_no(Fuel.ADBLUE, item, "finland/adblue" in fuels or "finland/adblueprivatecars" in fuels)

                # EV charging
                chargings = station.get("chargings") or []
                services = station.get("services") or []
                apply_yes_no(
                    Fuel.ELECTRIC,
                    item,
                    "finland/evCharging" in services or "finland/evCharging" in chargings,
                )

                # Truck access and facilities
                trucks = station.get("trucks") or []
                apply_yes_no(
                    Access.HGV,
                    item,
                    any(
                        code in trucks
                        for code in [
                            "finland/truckfuelingpoint",
                            "finland/trucklengthunder14",
                            "finland/trucklengthunder2525",
                            "finland/trucklengthunder345",
                        ]
                    ),
                )
                # AdBlue pump for trucks (in addition to fuel flag above)
                apply_yes_no(Fuel.ADBLUE, item, "finland/adblue" in trucks)

                # Other services
                # Car wash - several Finnish-specific car wash types
                apply_yes_no(
                    Extras.CAR_WASH,
                    item,
                    any(
                        code in services
                        for code in [
                            "finland/selfservicecarwash",
                            "finland/perfectcarwash",
                            "finland/perfectcarwash24hours",
                            "finland/othercarwash",
                        ]
                    ),
                )
                # Food / restaurant-style offers
                apply_yes_no(
                    "food",
                    item,
                    any(
                        code in services
                        for code in [
                            "finland/helmisimpukka",
                            "finland/helmisimpukkarestaurant",
                            "finland/breakfastbuffet",
                            "finland/lunch",
                            "finland/weekendlunch",
                            "finland/burgerking",
                            "finland/kotipizza",
                            "finland/pizza",
                        ]
                    ),
                )

                apply_category(Categories.FUEL_STATION, item)

                yield item
