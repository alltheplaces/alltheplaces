from datetime import datetime
from typing import Iterable
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature


class PowerNOSpider(Spider):
    name = "power_no"
    item_attributes = {"brand": "Power", "brand_wikidata": "Q137773608"}
    start_urls = ["https://www.power.no/api/v2/stores/header-stores?postalCode=1482&amount=500"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for store in response.json():
            item = DictParser.parse(store)
            item["street_address"] = item.pop("addr_full")

            item["ref"] = store["storeId"]
            item["branch"] = item.pop("name").removeprefix("POWER ")
            item["website"] = urljoin("https://www.power.no", store["storeUrl"])
            item["extras"]["ref:google:place_id"] = store.get("googleMapsPlaceId")

            item["opening_hours"] = OpeningHours()
            for schedule in store.get("workingSchedule", []):
                if hours := schedule.get("hours"):
                    date = datetime.fromisoformat(schedule["date"])
                    day = date.strftime("%A")
                    open_time, close_time = hours.split(" - ")
                    # Some times are "10" and others are "10:00"
                    if ":" not in open_time:
                        open_time += ":00"
                    if ":" not in close_time:
                        close_time += ":00"
                    item["opening_hours"].add_range(day, open_time, close_time)

            apply_category(Categories.SHOP_ELECTRONICS, item)
            yield item
