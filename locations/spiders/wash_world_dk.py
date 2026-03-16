import re
from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class WashWorldDKSpider(Spider):
    name = "wash_world_dk"
    item_attributes = {"brand": "Wash World", "brand_wikidata": "Q130249954"}
    start_urls = ["https://washworld.dk/wp-json/ww/v1/locations"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["state"] = location["region_name"]

            item["ref"] = location["post_id"]
            item["lat"] = location["coordinates"]["y"]
            item["lon"] = location["coordinates"]["x"]
            item["image"] = location["image"]
            item["extras"]["start_date"] = location["soft_opening"]

            if m := re.match(r"([ \w]+) (\d+\w?), (\d+) ([ \w]+)$", location["address"]):
                item["street"], item["housenumber"], item["postcode"], item["city"] = m.groups()

            apply_category(Categories.CAR_WASH, item)

            yield item
