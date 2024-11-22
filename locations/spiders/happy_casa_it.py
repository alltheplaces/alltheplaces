from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours, sanitise_day
from locations.items import set_closed


class HappyCasaITSpider(Spider):
    name = "happy_casa_it"
    item_attributes = {"brand": "Happy Casa", "brand_wikidata": "Q126901260"}
    start_urls = ["https://www.happycasastore.it/hcs_data_json.php?token=3614c6c584893cf119ef134d8fbe9abf"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["lat"], item["lon"] = location["marker_coordinate"].split(",")
            item["branch"] = location["pdv"]
            item["extras"]["start_date"] = location["data_apertura"]
            item["extras"]["store_type"] = location["signboard"]

            item["opening_hours"] = OpeningHours()
            for rule in location["orari"][0]:
                if rule == "CHIUSO":
                    item["opening_hours"].add_range(sanitise_day(day, DAYS_IT), "closed", "closed")
                    continue
                day, times = rule.split(" ", 1)
                for time in times.replace("  ", "-").split(" "):
                    if "CHIUSO" not in time:
                        item["opening_hours"].add_range(sanitise_day(day, DAYS_IT), *time.split("-"))

            if location["stato_pv"] == "chiuso":
                set_closed(item)

            yield item
