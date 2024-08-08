from typing import Any

import chompjs
from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature


class UpimSpider(Spider):
    name = "upim"
    UPIM = {"brand": "Upim", "brand_wikidata": "Q1414836"}
    BLUKIDS = {"brand": "Blukids", "name": "Blukids"}
    start_urls = ["https://stores.upim.com/js_db/locations-1.js"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in chompjs.parse_js_object(response.text):
            item = Feature()
            item["ref"] = location["id"]
            item["lat"] = location["lat"]
            item["lon"] = location["lon"]
            item["name"] = location["name"]
            item["street_address"] = location["a1"]
            item["city"] = location["city"]
            item["state"] = location["prov"]
            item["postcode"] = location["cap"]
            item["country"] = location["country_tag"]
            item["website"] = location["l"]
            item["phone"] = location["phone"]

            if item["name"].upper().startswith("UPIM"):
                item["branch"] = item.pop("name").split(" ", 1)[1]
                item.update(self.UPIM)
            elif item["name"].upper().startswith("BLUKIDS"):
                item["branch"] = item.pop("name").split(" ", 1)[1].removesuffix(" Bk")
                item.update(self.BLUKIDS)
                apply_category(Categories.SHOP_CLOTHES, item)

            yield item
