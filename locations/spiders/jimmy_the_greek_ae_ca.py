from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.storerocket import StoreRocketSpider


class JimmyTheGreekAECASpider(StoreRocketSpider):
    name = "jimmy_the_greek_ae_ca"
    item_attributes = {"brand": "Jimmy the Greek", "brand_wikidata": "Q17077817"}
    storerocket_id = "BrJq9MkJqE"

    def parse_item(self, item: Feature, location: dict, **kwargs):
        apply_category(Categories.FAST_FOOD.value | {"cuisine": "greek", "takeaway": "yes"}, item)
        yield item
