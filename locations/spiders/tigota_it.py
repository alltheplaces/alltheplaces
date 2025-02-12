from typing import Any, Iterable

from scrapy import Request
from scrapy.http import JsonRequest, Response
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours, sanitise_day


class TigotaITSpider(Spider):
    name = "tigota_it"
    item_attributes = {"brand": "Tigotà", "brand_wikidata": "Q107464330"}

    def start_requests(self) -> Iterable[Request]:
        yield JsonRequest(
            url="https://gom.gottardospa.it/negozi/shops",
            headers={
                "client_id": "f291b9b6c427444593ee7d209e04010c",
                "client_secret": "5B5d2218c3054fcab64bBBab769FB865",
            },
        )

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            for k in list(location.keys()):
                location[k.removeprefix("shop_")] = location.pop(k)
            item = DictParser.parse(location)
            item["street_address"] = item.pop("addr_full")
            item["addr_full"] = location.get("marketing_address")
            item["website"] = "https://www.tigota.it/negozi/{}".format(item["ref"])
            item["extras"]["start_date"] = location["opening_date"]

            item["opening_hours"] = OpeningHours()
            for rule in location.get("weekly_opening_hours", []):
                for times in rule["shop_opening_week_hours"]:
                    item["opening_hours"].add_range(
                        sanitise_day(rule["shop_opening_week_day"], DAYS_IT), *times.split(" - ")
                    )
            yield item
