import re
from typing import AsyncIterator

from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser


class BodystreetSpider(Spider):
    name = "bodystreet"
    item_attributes = {"brand": "Bodystreet", "brand_wikidata": "Q117880186"}

    async def start(self) -> AsyncIterator[JsonRequest]:
        yield JsonRequest(
            url="https://www.bodystreet.com/api/v1/entries/entrysearch",
            method="POST",
        )

    def parse(self, response, **kwargs):
        for result in response.json()["hits"]:
            if result.get("itemType") == "entry":
                item = DictParser.parse(result)
                item["ref"] = result.get("_id")
                if item.get("street"):
                    item["street_address"] = (
                        item.pop("street") if re.search(r"\d+", item["street"]) else item.get("street_address")
                    )
                item["addr_full"] = result.get("addressString")
                slug = result.get("slug")
                item["website"] = (
                    "https://www.bodystreet.com/de/studio/" + slug if slug else "https://www.bodystreet.com"
                )
                apply_category(Categories.GYM, item)

                yield item
