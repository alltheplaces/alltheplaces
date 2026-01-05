from typing import Any

from scrapy import Spider
from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser


class SmileysDESpider(Spider):
    name = "smileys_de"
    item_attributes = {"brand": "Smiley's", "brand_wikidata": "Q60998945"}
    start_urls = ["https://shop.smileys.de/api/v1/stores"]

    def parse(self, response: Response, **kwargs: Any) -> Any:
        for location in response.json()["data"]["stores"]:
            location.update(location.pop("address"))
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["extras"]["fax"] = location.get("fax")

            apply_yes_no(Extras.TAKEAWAY, item, location["modes"]["pickup"])
            apply_yes_no(Extras.DELIVERY, item, location["modes"]["delivery"])

            apply_category(Categories.FAST_FOOD, item)

            yield item
