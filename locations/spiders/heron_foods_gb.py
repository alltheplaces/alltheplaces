from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class HeronFoodsGBSpider(AgileStoreLocatorSpider):
    name = "heron_foods_gb"
    item_attributes = {"brand": "Heron Foods", "brand_wikidata": "Q5743472"}
    allowed_domains = ["heronfoods.com"]

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item["branch"] = item.pop("name")
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
