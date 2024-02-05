from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SmilebrandsSpider(WPStoreLocatorSpider):
    name = "smilebrands"
    item_attributes = {"brand": "Smile Brands Inc.", "brand_wikidata": "Q108286823"}
    allowed_domains = ["smilebrands.com"]

    def parse_item(self, item: Feature, location: dict, **kwargs):
        apply_category(Categories.DENTIST, item)
        yield item
