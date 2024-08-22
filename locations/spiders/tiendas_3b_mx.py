from typing import Iterable

from scrapy.http import Response

from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class Tiendas3bMXSpider(AgileStoreLocatorSpider):
    name = "tiendas_3b_mx"
    item_attributes = {
        "brand_wikidata": "Q113217378",
        "brand": "Tiendas 3B",
    }
    allowed_domains = [
        "tiendas3b.com",
    ]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        # See https://github.com/alltheplaces/alltheplaces/pull/9359#issuecomment-2272497115
        # Item names were very low quality
        item["name"] = None
        yield item
