from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import DAYS, OpeningHours


class SparFRSpider(Spider):
    name = "spar_fr"
    item_attributes = {"brand": "Spar", "brand_wikidata": "Q610492"}
    start_urls = ["https://magasins.spar.fr/api/v3/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["lat"] = location["address"]["latitude"]
            item["lon"] = location["address"]["longitude"]
            item["website"] = location["contact"]["url"]

            item["opening_hours"] = OpeningHours()
            for rule in location["businessHours"]:
                item["opening_hours"].add_range(
                    DAYS[rule["startDay"] - 1], rule["openTimeFormat"], rule["closeTimeFormat"]
                )

            if location["brand"] == "SPAR-Supermarche":
                apply_category(Categories.SHOP_SUPERMARKET, item)
            else:
                apply_category(Categories.SHOP_CONVENIENCE, item)

            yield item
