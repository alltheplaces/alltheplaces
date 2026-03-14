from typing import Iterable

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_go_maps import WpGoMapsSpider


class EzMartUSSpider(WpGoMapsSpider):
    item_attributes = {"brand": "EZ Mart"}
    name = "ez_mart_us"
    allowed_domains = ["blarneycastleoil.com"]

    def post_process_item(self, item: Feature, location: dict) -> Iterable[Feature]:
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
