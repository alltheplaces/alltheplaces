from typing import Any
from urllib.parse import urljoin

from scrapy import Spider
from scrapy.http import JsonRequest, Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.spiders.dino_pl import populate


class LunchGardenBESpider(Spider):
    name = "lunch_garden_be"
    item_attributes = {"brand": "Lunch Garden", "brand_wikidata": "Q2491217"}
    start_urls = ["https://www.lunchgarden.be/nl/restaurants"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        yield JsonRequest(
            url=urljoin(response.url, response.xpath('//*[@type="application/json"]/@data-src').get()),
            callback=self.parse_location,
        )

    def parse_location(self, response: Response, **kwargs: Any) -> Any:
        for location in populate(0, response.json())["data"][1]["restaurants-nl"]:
            item = DictParser.parse(location)
            item["ref"] = location["_id"]
            item["branch"] = item.pop("name").removeprefix("Lunch Garden ")
            item["website"] = urljoin("https://www.lunchgarden.be/nl/restaurants/", location["slug"])

            apply_yes_no(Extras.WHEELCHAIR, item, "accessible" in location["facilities"])
            apply_yes_no(Extras.TAKEAWAY, item, "takeaway" in location["facilities"])
            apply_yes_no(Extras.WIFI, item, "wifi" in location["facilities"])

            apply_category(Categories.RESTAURANT, item)

            yield item
