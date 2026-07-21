from collections import Counter
from datetime import datetime
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class ErsteBankHUSpider(Spider):
    name = "erste_bank_hu"
    item_attributes = {"brand": "Erste Bank", "brand_wikidata": "Q696867"}

    async def start(self) -> AsyncIterator[Any]:
        for location_type in ("BRANCH", "ATM"):
            yield JsonRequest(
                url=f"https://www.erstebank.hu/bin/erstegroup/gemesgapi/locations/gem_site_location_locations-hu-ebh?types={location_type}&items=1000&page=0&language=hu&longitude=19.040235&latitude=47.497912",
                cb_kwargs={"location_type": location_type},
            )

    def parse(self, response: Response, location_type: str, **kwargs: Any) -> Any:
        for poi in response.json():
            item = DictParser.parse(poi)
            item["ref"] = poi["ouId"]
            item["street_address"] = item.pop("street", None)  # address.street includes the house number
            item.pop("name", None)  # title is always the brand
            item.pop("state", None)  # address.state is a NUTS statistical region, not an addr:state
            item.pop("country", None)  # single-country spider; country is derived from the spider name

            accessibility = {entry.get("id") for entry in poi.get("accessibilityInformation") or []}
            apply_yes_no(Extras.WHEELCHAIR, item, "appointmentBarrierFree" in accessibility)

            if opening_hours := self.parse_hours(poi.get("openingHoursWithDates")):
                item["opening_hours"] = opening_hours

            if location_type == "BRANCH":
                item["branch"] = poi.get("description")
                apply_category(Categories.BANK, item)
            elif location_type == "ATM":
                item["name"] = (poi.get("description") or "").removesuffix(" ATM") or None
                services = {service.get("id") for service in poi.get("services") or []}
                apply_yes_no(Extras.CASH_IN, item, "atmDeposit" in services)
                apply_category(Categories.ATM, item)

            yield item

    def parse_hours(self, opening_hours_with_dates: list | None) -> OpeningHours | None:
        if not opening_hours_with_dates:
            return None
        # The feed gives dated opening times; collapse them to the most common periods per weekday.
        by_day: dict[int, Counter] = {}
        try:
            for entry in opening_hours_with_dates:
                day_index = datetime.strptime(entry["date"], "%d.%m.%Y").weekday()
                periods = tuple((p["open"], p["close"]) for p in entry.get("periods") or [])
                by_day.setdefault(day_index, Counter())[periods] += 1

            hours = OpeningHours()
            for day_index, counter in by_day.items():
                periods = counter.most_common(1)[0][0]
                if not periods:
                    hours.set_closed(DAYS[day_index])
                else:
                    for open_time, close_time in periods:
                        hours.add_range(DAYS[day_index], open_time, close_time)
        except (KeyError, ValueError) as error:
            self.logger.warning("Could not parse hours: {}".format(error))
            return None
        return hours or None
