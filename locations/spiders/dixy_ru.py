from typing import Any

import scrapy
from scrapy.http import Response

from locations.hours import OpeningHours
from locations.items import Feature


class DixyRUSpider(scrapy.Spider):
    name = "dixy_ru"
    item_attributes = {"brand": "Дикси", "brand_wikidata": "Q4161561"}
    start_urls = ["https://dixy.ru/ajax/stores-json.php"]
    custom_settings = {"ROBOTSTXT_OBEY": False}

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for store in response.json():
            store.update(store.pop("properties"))
            item = Feature()
            item["ref"] = store["id"]
            item["addr_full"] = store["balloonContentBody"]
            item["lat"], item["lon"] = store["geometry"]["coordinates"]
            item["website"] = "https://dixy.ru/"
            item["opening_hours"] = OpeningHours()
            if store["balloonContentFooter"] == "Круглосуточно":
                item["opening_hours"] = "24/7"
            else:
                item["opening_hours"].add_ranges_from_string(f'Mo-Su {store["balloonContentFooter"]}')
            yield item
