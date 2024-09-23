from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories
from locations.items import Feature
from locations.storefinders.closeby import ClosebySpider


class UniversalStoreAUSpider(ClosebySpider):
    name = "universal_store_au"
    item_attributes = {"brand": "Universal Store", "brand_wikidata": "Q96412731", "extras": Categories.SHOP_CLOTHES.value}
    api_key = "87aa802ed1754c56a156df516b2d65ed"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        if branch_name := item.pop("name", None):
            item["branch"] = branch_name
        yield item
