from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class ElectrochargeBGSpider(Spider):
    name = "electrocharge_bg"
    item_attributes = {"brand": "Electrocharge", "brand_wikidata": "Q133307258"}
    allowed_domains = ["electrocharge.bg"]
    start_urls = ["https://electrocharge.bg/bg/electrocharge/fetch_charging_stations/"]
    no_refs = True

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for station in response.json()["stations"]:
            item = Feature()
            item["addr_full"] = station["location"]
            item["lat"] = station["coordinates"]["lat"]
            item["lon"] = station["coordinates"]["lng"]

            apply_category(Categories.CHARGING_STATION, item)

            yield item
