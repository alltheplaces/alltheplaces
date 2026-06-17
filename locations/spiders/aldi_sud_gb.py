from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AldiSudGBSpider(UberallSpider):
    name = "aldi_sud_gb"
    item_attributes = {"brand_wikidata": "Q41171672", "country": "GB"}
    key = "gPbSx6NN9vcpTZwrCb8waXmtoJo9MN"

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item["name"] = item["phone"] = None

        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
