from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class MirabitoUSSpider(AgileStoreLocatorSpider):
    name = "mirabito_us"
    item_attributes = {"brand": "Mirabito", "brand_wikidata": "Q126489051"}
    allowed_domains = ["www.mirabitostores.com"]
    drop_attributes = {"website"}

    def post_process_item(self, item: Feature, response: TextResponse, feature: dict) -> Iterable[Feature]:
        item.pop("name")
        item["branch"] = feature["description"]
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
