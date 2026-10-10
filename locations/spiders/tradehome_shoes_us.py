from typing import Iterable

from scrapy.http import TextResponse

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.locally import LocallySpider


class TradehomeShoesUSSpider(LocallySpider):
    name = "tradehome_shoes_us"
    item_attributes = {"brand": "Tradehome Shoes", "brand_wikidata": "Q120599540", "name": "Tradehome Shoes"}
    company_id = 15946
    categories = [""]

    def post_process_item(self, item: Feature, response: TextResponse, location: dict) -> Iterable[Feature]:
        item.pop("name", None)
        item["street_address"] = item.pop("addr_full")
        if " - " in item["city"]:
            item["city"], branch = item["city"].split(" - ", 1)
            item["branch"] = branch
        apply_category(Categories.SHOP_SHOES, item)
        yield item
