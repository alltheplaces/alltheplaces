import json
from typing import Iterable

from scrapy import Spider
from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class EriksDeliCafeUSSpider(Spider):
    name = "eriks_deli_cafe_us"
    item_attributes = {"brand": "Erik's DeliCafé", "brand_wikidata": "Q116922917"}
    start_urls = ["https://sl-front.proguscommerce.com/api/locations?shopId=5399"]

    def parse(self, response: TextResponse) -> Iterable[Feature]:
        for location in response.json():
            item = DictParser.parse(location)
            item["branch"] = item.pop("name")
            item["extras"]["website:menu"] = item.pop("website")
            for field in json.loads(location["customFields"]):
                if field["id"] == 610:
                    item["website"] = field["value"]
            apply_category(Categories.FAST_FOOD, item)
            yield item
