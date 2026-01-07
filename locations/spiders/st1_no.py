from typing import AsyncIterator, Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Access, Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range
from locations.items import Feature


class St1NOSpider(Spider):
    name = "st1_no"
    allowed_domains = ["st1.no"]
    item_attributes = {
        "brand": "St1",
        "brand_wikidata": "Q7592214",
    }

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://st1.no/proxy/cms-view/v1/content/page?path=finn-stasjon",
            headers={"x-st1-locale": "no-NO"},
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
                    item["website"] = urljoin("https://st1.no/", path)

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
                fuels = station.get("fuels")
                apply_yes_no(Fuel.DIESEL, item, "norway/diesel" in fuels)
                apply_yes_no(Fuel.OCTANE_95, item, "norway/95bensin" in fuels)
                apply_yes_no(Fuel.OCTANE_98, item, "norway/98bensin" in fuels)
                apply_yes_no(Fuel.BIODIESEL, item, "norway/hvo100" in fuels)
                apply_yes_no(Fuel.UNTAXED_DIESEL, item, "norway/coloredagoonpump" in fuels)
                apply_yes_no(Fuel.HGV_DIESEL, item, "norway/truckdiesel" in fuels)

                # EV charging
                chargings = station.get("chargings")
                services = station.get("services")
                apply_yes_no(Fuel.ELECTRIC, item, "norway/evcharging" in chargings or "norway/elcharging" in services)

                # Truck access and facilities
                trucks = station.get("trucks")
                apply_yes_no(
                    Access.HGV, item, any(t in trucks for t in ["norway/truckfacilities", "norway/truckparking"])
                )
                apply_yes_no(Fuel.ADBLUE, item, "norway/truckadblue" in fuels)

                # Other services
                apply_yes_no(
                    Extras.CAR_WASH,
                    item,
                    any(s in services for s in ["norway/carwash", "norway/norwegianshellcarwash"]),
                )
                apply_yes_no("emergency:defibrillator", item, "norway/defibrillator" in services)
                apply_yes_no("food", item, "norway/realfood" in services)

                apply_category(Categories.FUEL_STATION, item)

                yield item
