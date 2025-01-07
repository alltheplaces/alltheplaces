from typing import Any

import scrapy
from scrapy.http import Response

from locations.dict_parser import DictParser
from locations.hours import DAYS_IT, OpeningHours


class PrixQualityITSpider(scrapy.Spider):
    name = "prix_quality_it"
    item_attributes = {"brand": "Prix", "brand_wikidata": "Q61994819"}
    start_urls = ["https://www.prixquality.com/wp-json/acf/v3/shop?per_page=999&orderby=title"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for record in response.json():
            store = record["acf"]
            item = DictParser.parse(store)
            item["ref"] = record["id"]
            item["street_address"] = store.get("address")
            item["branch"] = store["shop_name"]
            item["opening_hours"] = OpeningHours()
            for day in DAYS_IT:
                if times := store.get(day.lower(), ""):
                    if "CHIUSO" in times:
                        item["opening_hours"].set_closed(DAYS_IT[day])
                    else:
                        for time in times.split("|"):
                            item["opening_hours"].add_range(DAYS_IT[day], *time.split("-"), time_format="%H:%M")
            yield item
