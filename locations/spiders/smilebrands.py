from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class SmilebrandsSpider(WPStoreLocatorSpider):
    name = "smilebrands"
    item_attributes = {"brand": "Smile Brands Inc.", "brand_wikidata": "Q108286823"}
    allowed_domains = ["smilebrands.com"]
