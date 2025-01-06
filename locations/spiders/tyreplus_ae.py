from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.spiders.tyreplus_au import TyreplusAUSpider


class TyreplusAESpider(TyreplusAUSpider):
    name = "tyreplus_ae"
    allowed_domains = ["www.tyreplus-me.com"]
    start_urls = ["https://www.tyreplus-me.com/en/uae/dealers"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if "Door to Door" in item["name"]:
            # Not a physical store.
            return
        item["branch"] = (
            item.pop("name")
            .removeprefix("TYREPLUS CME - ")
            .removeprefix("TYREPLUS CME -")
            .removeprefix("TYREPLUS CTC ")
            .removeprefix("TYREPLUS EM - ")
            .removeprefix("TYREPLUS EM ")
            .removeprefix("TYREPLUS ")
            .removeprefix("Tyreplus ")
        )
        apply_category(Categories.SHOP_TYRES, item)
        yield item
