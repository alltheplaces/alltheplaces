from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.pipelines.address_clean_up import merge_address_lines
from locations.storefinders.stockist import StockistSpider


class TedsCameraStoresAUSpider(StockistSpider):
    name = "teds_camera_stores_au"
    item_attributes = {"brand": "Ted's Camera Stores", "brand_wikidata": "Q117958394"}
    key = "map_7q5z92n3"

    def parse_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        item["street_address"] = merge_address_lines([location["address_line_2"], item["street_address"]])
        apply_category(Categories.SHOP_CAMERA, item)
        yield item
