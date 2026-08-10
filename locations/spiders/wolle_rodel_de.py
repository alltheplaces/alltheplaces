import re
from typing import Any, Iterable

from scrapy import Spider
from scrapy.http import Response

from locations.categories import apply_category
from locations.dict_parser import DictParser
from locations.items import Feature


class WolleRodelDESpider(Spider):
    name = "wolle_rodel_de"
    item_attributes = {
        "brand_wikidata": "Q107357091",
        "brand": "Wolle Rödel",
    }
    allowed_domains = ["www.wolle-roedel.com"]
    start_urls = ["https://www.wolle-roedel.com/StoreLocator/getStores"]

    def parse(self, response: Response, **kwargs: Any) -> Iterable[Feature]:
        for location in response.json()["data"]:
            location.pop("email", None)
            item = DictParser.parse(location)

            branch = location["label"].removeprefix("Wolle Rödel").strip()
            if host := re.search(r"\s*\(([^)]+)\)\s*$", branch):
                item["located_in"] = host.group(1).removeprefix("im ").strip()
                branch = branch[: host.start()].strip()
            item["branch"] = branch

            apply_category({"shop": "fabric"}, item)
            yield item
