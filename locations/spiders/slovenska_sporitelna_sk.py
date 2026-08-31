from collections import Counter
from datetime import datetime
from typing import Any, AsyncIterator

from scrapy import Spider
from scrapy.http import Request, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import DAYS, OpeningHours
from locations.items import Feature


class SlovenskaSporitelnaSKSpider(Spider):
    name = "slovenska_sporitelna_sk"
    item_attributes = {"brand": "Slovenská sporiteľňa", "brand_wikidata": "Q7541907"}

    async def start(self) -> AsyncIterator[Any]:
        for poi_type in ("pobocka", "bankomat", "firemnecentrum", "vkladomat"):
            yield Request(
                url=f"https://www.slsp.sk/bin/erstegroup/gemesgapi/locations/gem_site_location_locations-sk-slsp?types={poi_type}&items=1000&page=0&longitude=17.1071553&latitude=48.1477745"
            )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for poi in response.json():
            # title is always the brand and address/location are nested, so build manually
            item = Feature()
            item["ref"] = poi["ouId"]
            item["branch"] = poi.get("description")
            address = poi.get("address") or {}
            item["street_address"] = address.get("street")
            item["city"] = address.get("city")
            item["postcode"] = address.get("zipCode")
            location = poi.get("location") or {}
            item["lat"] = location.get("latitude")
            item["lon"] = location.get("longitude")
            service_ids = {s.get("id") for s in poi.get("services", [])}

            if poi["types"][1] == "BRANCH":
                apply_category(Categories.BANK, item)
                apply_yes_no(Extras.ATM, item, "atmInBranch" in service_ids)
            elif poi["types"][1] == "ATM":
                apply_category(Categories.ATM, item)
                apply_yes_no(Extras.CASH_IN, item, "banknoteDeposit" in service_ids)
            else:
                self.logger.error("Unexpected SLSP category: %s", poi["types"][1])
                continue

            if hours := poi.get("openingHoursWithDates"):
                try:
                    item["opening_hours"] = self.parse_opening_hours(hours)
                except Exception:
                    self.logger.warning("Failed to parse hours for %s", item["ref"])

            yield item

    def parse_opening_hours(self, opening_hours_with_dates: list) -> OpeningHours:
        by_day: dict[int, Counter] = {}
        for entry in opening_hours_with_dates:
            day_index = datetime.strptime(entry["date"], "%d.%m.%Y").weekday()
            periods = tuple((p["open"], p["close"]) for p in entry.get("periods", []))
            by_day.setdefault(day_index, Counter())[periods] += 1

        oh = OpeningHours()
        for day_index, counter in by_day.items():
            most_common_periods = counter.most_common(1)[0][0]
            if not most_common_periods:
                oh.set_closed(DAYS[day_index])
            else:
                for open_time, close_time in most_common_periods:
                    oh.add_range(DAYS[day_index], open_time, close_time)
        return oh
