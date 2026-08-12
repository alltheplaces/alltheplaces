from typing import Any

from scrapy import Request, Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class DrMartensSpider(Spider):
    name = "dr_martens"
    item_attributes = {"brand": "Dr. Martens", "brand_wikidata": "Q1126126"}
    start_urls = ["https://www.drmartens.com/uk/en_gb/store-finder?q=&page=0&latitude=0&longitude=0"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        per_page = 10
        pages = -(-response.json()["total"] // per_page)
        for i in range(0, pages):
            yield Request(
                url=f"https://www.drmartens.com/uk/en_gb/store-finder?q=&page={i}&latitude=0&longitude=0",
                callback=self.parse_stores,
            )

    def parse_stores(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]:
            location["street_address"] = ", ".join(filter(None, [location["line1"], location["line2"]]))
            location["phone"] = location["phone1"]
            location["id"] = location.pop("url").split("?")[0]  # drop the empty lat/long query
            item = DictParser.parse(location)
            item["branch"] = location["displayName"].replace("Dr. Martens ", "")
            apply_category(Categories.SHOP_SHOES, item)
            item.pop("name")
            try:
                oh = OpeningHours()
                for day, times in location.get("openings", {}).items():
                    if times in ["Closed", " - "]:
                        continue
                    start_time, end_time = times.split(" - ")
                    oh.add_range(day, start_time, end_time)
                item["opening_hours"] = oh
            except Exception:
                pass
            yield item
