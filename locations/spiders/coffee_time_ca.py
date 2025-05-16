from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.momentfeed import MomentFeedSpider


class CoffeeTimeCASpider(MomentFeedSpider):
    name = "coffee_time_ca"
    item_attributes = {"brand": "Coffee Time", "brand_wikidata": "Q5140932"}
    api_key = "YDGUJSNDOUAFKPRL"

    def parse_item(self, item: Feature, feature: dict, store_info: dict):
        item.pop("email", None)
        apply_category(Categories.CAFE, item)
        yield item
