from typing import Any

from scrapy.http import Response
from scrapy.spiders import Spider

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class JigsawGBSpider(Spider):
    name = "jigsaw_gb"
    item_attributes = {"brand": "Jigsaw", "brand_wikidata": "Q6192383"}
    start_urls = ["https://www.jigsaw-online.com/cdn/shop/t/619/assets/jigsaw-stores.json"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["features"]:
            newlocation = {key.replace("branch_", ""): value for key, value in location["properties"].items()}
            item = DictParser.parse(newlocation)
            item["branch"] = newlocation["name"]
            item["name"] = None
            item["street_address"] = newlocation["address_2"]
            item["lon"], item["lat"] = location["geometry"]["coordinates"]

            opening_hours = OpeningHours()
            oh = newlocation["opening_hours"]
            oh = oh.replace("</li><li>", ", ")
            oh = oh.replace("<li>", "")
            oh = oh.replace("</li>", "")
            for range in oh.split(", "):
                day, time_range = range.split(": ")
                time_range = time_range.replace(" ", "")
                if "closed" not in time_range.lower():
                    open_time, close_time = time_range.split("-")
                    opening_hours.add_range(day, open_time, close_time)
            item["opening_hours"] = opening_hours

            apply_category(Categories.SHOP_CLOTHES, item)
            yield item
