from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.uberall import UberallSpider


class AlltownUSSpider(UberallSpider):
    name = "alltown_us"
    item_attributes = {"brand": "Alltown", "brand_wikidata": "Q119586667"}
    key = "gNsMTlc7niXPwZnJ8s9NlD1eR5Z6b3"

    def post_process_item(self, item: Feature, response: Response, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
