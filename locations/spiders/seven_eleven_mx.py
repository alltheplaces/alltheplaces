from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.seven_eleven_au import SEVEN_ELEVEN_SHARED_ATTRIBUTES


class SevenElevenMXSpider(Spider):
    name = "seven_eleven_mx"
    item_attributes = SEVEN_ELEVEN_SHARED_ATTRIBUTES
    start_urls = ["https://app.7-eleven.com.mx:8443/web/services/tiendas"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["results"]:
            item = Feature()
            item["ref"] = location["id"]
            item["addr_full"] = location["full_address"]
            item["branch"] = location["name"]
            item["lat"] = location["latitude"]
            item["lon"] = location["longitude"]

            if location["open_hours"].lower() == "24 horas":
                item["opening_hours"] = "24/7"

            if location["type"] == 1:
                apply_category(Categories.FUEL_STATION, item)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
