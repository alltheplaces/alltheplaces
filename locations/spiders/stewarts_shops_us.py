from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.momentfeed import MomentFeedSpider


class StewartsShopsUSSpider(MomentFeedSpider):
    name = "stewarts_shops_us"
    item_attributes = {"brand": "Stewart's Shops", "brand_wikidata": "Q7615690"}
    api_key = "ZGRQTRLWHXDMDNUO"

    def parse_item(self, item: Feature, feature: dict, store_info: dict):
        apply_category(Categories.SHOP_CONVENIENCE, item)
        yield item
