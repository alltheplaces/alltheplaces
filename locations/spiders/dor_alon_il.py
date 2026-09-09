import re
from typing import Any, Iterable

from chompjs import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, Fuel, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class DorAlonILSpider(Spider):
    name = "dor_alon_il"
    item_attributes = {"brand": "דור אלון", "brand_wikidata": "Q16130352"}
    allowed_domains = ["www.doralon.co.il"]
    start_urls = ["https://www.doralon.co.il/station/"]
    requires_proxy = True  # doralon.co.il is unreachable from the crawl datacenter without an Israel exit

    # station flag (value "1") -> tag
    SERVICES = {
        "gaz98": Fuel.OCTANE_98,  # בנזין 98
        "gaz_station": Fuel.LPG,  # גז (autogas)
        "masheva_oreaa": Fuel.ADBLUE,  # משאבת אוריאה (AdBlue pump)
        "electric_cars": Fuel.ELECTRIC,
        "car_wash": Extras.CAR_WASH,
    }
    # Israeli opening-hours fields: the working week is Sunday-Thursday, then Friday and Saturday.
    HOURS = {
        "station_hours_week": ["Su", "Mo", "Tu", "We", "Th"],
        "station_hours_friday": ["Fr"],
        "station_hours_saturday": ["Sa"],
    }

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        if (start := response.text.find("var stations =")) == -1:
            self.logger.error("Dor Alon: station data not found")
            return
        for station in chompjs.parse_js_object(response.text[start:]):
            item = DictParser.parse(station)  # id -> ref, title -> name, lat/lng, address -> addr_full
            item["ref"] = str(item["ref"])
            item["branch"] = item.pop("name", None)  # the brand name comes from NSI
            item["street_address"] = item.pop("addr_full", None)
            item["phone"] = station.get("station_phone")
            item["opening_hours"] = self.parse_hours(station)
            apply_category(Categories.FUEL_STATION, item)

            for field, tag in self.SERVICES.items():
                apply_yes_no(tag, item, str(station.get(field)) == "1")

            yield item

    def parse_hours(self, station: dict) -> OpeningHours:
        oh = OpeningHours()
        for field, days in self.HOURS.items():
            value = station.get(field)
            if not value or value == "None":
                continue
            for day in days:
                try:
                    if value == "24":
                        oh.add_range(day, "00:00", "24:00")
                    elif value == "סגור":  # closed
                        oh.set_closed(day)
                    elif hours := re.match(r"^(\d{1,2}:\d{2})-(\d{1,2}:\d{2})$", value):
                        oh.add_range(day, hours.group(1), hours.group(2))
                except (TypeError, ValueError):  # non-string or unparseable value
                    self.crawler.stats.inc_value("atp/{}/hours/failed".format(self.name))
        return oh
