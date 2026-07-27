from locations.categories import Categories, apply_category
from locations.storefinders.storerocket import StoreRocketSpider


class BillyTacosSpider(StoreRocketSpider):
    name = "billy_tacos"
    item_attributes = {"brand": "Billy Tacos", "brand_wikidata": "Q122167398"}
    storerocket_id = "2rpXRR0JB5"
    
    def parse_item(self, item, location):
        apply_category(Categories.FAST_FOOD, item)
        item["extras"]["cuisine"] = "mexican;taco"
        yield item
