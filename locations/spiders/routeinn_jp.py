from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.goga_store_locator import GogaStoreLocatorSpider


class RouteinnJPSpider(GogaStoreLocatorSpider):
    name = "routeinn_jp"
    item_attributes = {"brand": "ホテルルートイン", "brand_wikidata": "Q11337912"}
    start_urls = ["https://route-inn.storelocator.jp/api/point"]
    geohashes = ["w", "x"]
    geohash_suffix = "/"

    def post_process_feature(self, item: Feature, source_feature: dict, **kwargs) -> Iterable[Feature]:
        item["branch"] = item.pop("name").removeprefix("ホテルルートイン")
        item["extras"]["branch:en"] = source_feature["name.en"].removeprefix("HOTEL ROUTE INN ").title()
        item["phone"] = f"+81 {source_feature['phone']}"
        item["website"] = source_feature["詳細ページへのリンク"]
        item["extras"]["website:booking"] = source_feature["予約ページURL（PC）"]
        apply_category(Categories.HOTEL, item)
        yield item
