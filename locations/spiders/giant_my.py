from scrapy import Selector

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.super_store_finder import SuperStoreFinderSpider


class GiantMYSpider(SuperStoreFinderSpider):
    name = "giant_my"
    item_attributes = {
        "brand_wikidata": "Q4217013",
        "brand": "Giant Hypermarket",
    }
    allowed_domains = [
        "www.giant.com.my",
    ]

    def parse_item(self, item: Feature, location: Selector):
        apply_category(Categories.SHOP_SUPERMARKET, item)
        yield item
