from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class BeisiaJPSpider(GogaStoreLocatorSpider):
    name = "beisia_jp"

    start_urls = ["https://map.beisia.co.jp/api/points"]
    item_attributes = {
        "brand": "ベイシア",
        "brand_wikidata": "Q11336776",
    }
    website_formatter = "https://map.beisia.co.jp/map/{}"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["name"] = "ベイシア"
        item["branch"] = source_feature.get("name")
        item["extras"]["branch:ja-Hira"] = source_feature.get("ふりがな")
        apply_category(Categories.SHOP_SUPERMARKET, item)

        yield item
