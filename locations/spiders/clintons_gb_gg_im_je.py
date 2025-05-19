from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class ClintonsGBGGIMJESpider(WPStoreLocatorSpider):
    name = "clintons_gb_gg_im_je"
    item_attributes = {"brand": "Clintons", "brand_wikidata": "Q5134299"}
    allowed_domains = ["clintonsretail.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name", None)
        apply_category(Categories.SHOP_GIFT, item)
        yield item
