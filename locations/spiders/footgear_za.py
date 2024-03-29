from locations.storefinders.wp_store_locator import WPStoreLocatorSpider


class FootgearZASpider(WPStoreLocatorSpider):
    name = "footgear_za"
    item_attributes = {"brand": "Footgear", "brand_wikidata": "Q116290280"}
    allowed_domains = ["www.footgear.co.za"]
